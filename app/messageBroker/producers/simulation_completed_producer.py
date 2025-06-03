from app.messageBroker.producers.base_producer import BaseProducer
from app.models.statuses_enums import EventType
from app.business_logic.topologies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.models.pageination_models import CursorPaginationRequest
from app.models.mapper import SimulationMapper
import asyncio
from app.models.topolgy_simulation_models import TopologySimulation
from typing import List, Set
from app.app_container import app_container
import traceback
from app.models.message_bus_models import OutboxPublisher

class SimulationCompletedProducer(BaseProducer):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        super().__init__(rabbitmq_manager, exchange_name, db, app_container.config().SIMULATION_QUEUE)
        self.topologies_simulations_bl = TopologiesSimulationsBusinessLogic(db)
        self._initialize_config()
        self._initialize_outbox_publisher()

    def _initialize_config(self):
        """Initialize producer configuration."""
        self.retry_delay = 10  # seconds
        self.page_size = 10

    def _initialize_outbox_publisher(self):
        """Initialize the outbox publisher with simulation completion specific configuration."""
        self.outbox_publisher = OutboxPublisher(
            max_parallel=1,  # Process one at a time to avoid overwhelming the system
            initial_delay=self.retry_delay,
            max_retries=3,
            retry_delay=self.retry_delay,
            batch_size_events_query=self.page_size,
            max_messages_to_publish=1
        )

    def _get_event_filter(self) -> dict:
        """Returns the filter for finding unhandled and unpublished simulation completion events."""
        return {
            "is_handled": False,
            "published": False,
            "event_type": EventType.SIMULATION_COMPLETED.value
        }

    async def _get_completed_simulations(self) -> List[TopologySimulation]:
        """Fetch completed simulations from the database."""
        return await self.topologies_simulations_bl.find_completed_simulations(
            CursorPaginationRequest(page=1, page_size=self.page_size)
        )

    async def _get_existing_completed_sim_ids(self, sim_ids: List[str]) -> Set[str]:
        """Get set of simulation IDs that already have completed events."""
        existing_events = await self.events_db.find_events_by_filter({
            "event_type": EventType.SIMULATION_COMPLETED,
            "after._id": {"$in": sim_ids}
        }, limit=100)

        return {
            event["after"]["_id"]
            for event in existing_events
            if event.get("after") and event["after"].get("_id")
        }

    async def filter_published_simulations(self, simulations: List[TopologySimulation]) -> List[TopologySimulation]:
        """
        Filter out simulations that already have completed events.
        Returns a list of simulations that need completion events.
        """
        if not simulations:
            return []

        sim_ids = [sim.sim_id for sim in simulations]
        existing_sim_ids = await self._get_existing_completed_sim_ids(sim_ids)
        
        return [sim for sim in simulations if sim.sim_id not in existing_sim_ids]

    async def _process_completed_simulations(self, simulations: List[TopologySimulation]) -> int:
        """
        Process completed simulations by converting them to events and storing them.
        Returns the number of events processed.
        """
        if not simulations:
            return 0

        self.logger.info(f"Processing {len(simulations)} completed simulations.")
        completed_simulations = SimulationMapper.simulations_to_events(
            simulations, 
            EventType.SIMULATION_COMPLETED
        )
        await self.events_db.store_events(completed_simulations)
        return len(completed_simulations)

    async def _fetch_events(self) -> List[dict]:
        """
        Override base class method to handle simulation completion specific logic.
        Instead of fetching events, it processes completed simulations.
        """
        # Get completed simulations
        simulations = await self._get_completed_simulations()
        if not simulations:
            self.logger.info("No completed simulations found.")
            return []

        # Filter out already processed simulations
        filtered_simulations = await self.filter_published_simulations(simulations)
        if not filtered_simulations:
            self.logger.info("No new completed simulations to process.")
            return []

        # Process the filtered simulations and return them as events
        processed_count = await self._process_completed_simulations(filtered_simulations)
        self.logger.info(f"Successfully processed {processed_count} completed simulations.")

        # Return the newly created events
        return await self.events_db.find_events_by_filter({
            "event_type": EventType.SIMULATION_COMPLETED.value,
            "published": False
        }, limit=processed_count)

