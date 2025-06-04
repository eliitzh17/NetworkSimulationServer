from app.messageBroker.producers.base_producer import BaseProducer
from app.models.statuses_enums import EventType, TopologyStatusEnum
from app.models.message_bus_models import OutboxPublisher
from app.app_container import app_container
from app.db.topologies_simulations_db import TopologiesSimulationsDB
from typing import List, Dict, Set
import asyncio
import traceback

class LinksProducer(BaseProducer):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        self.config = app_container.config()
        super().__init__(rabbitmq_manager, exchange_name, db, self.config.RUN_LINKS_QUEUE)
        self.simulation_db = TopologiesSimulationsDB(db)
        self._initialize_outbox_publisher()

    def _initialize_outbox_publisher(self):
        """Initialize the outbox publisher with link-specific configuration."""
        self.outbox_publisher = OutboxPublisher(
            initial_delay=self.config.INITIAL_DELAY,
            max_retries=self.config.MAX_RETRIES,
            retry_delay=self.config.RETRY_DELAY,
            batch_size_events_query=self.config.PAGE_SIZE,
            max_messages_to_publish=self.config.MAX_LINKS_IN_PARALLEL_PRODUCER
        )

    def _get_event_filter(self) -> dict:
        """Returns the filter for finding unhandled and unpublished link events."""
        return {
            "published": False,
            "event_type": EventType.LINK_RUN.value
        }

    async def _group_events_by_simulation(self, events: List[dict]) -> Dict[str, List[dict]]:
        """Groups events by their simulation ID."""
        events_by_simulation = {}
        for event in events:
            sim_id = event.get('sim_id')
            events_by_simulation.setdefault(sim_id, []).append(event)
        return events_by_simulation

    async def _get_running_simulations(self, simulation_ids: List[str]) -> List[dict]:
        """Retrieves running simulations for the given IDs."""
        return await self.simulation_db.get_simulations_by_ids_and_status(
            simulation_ids,
            [TopologyStatusEnum.running]
        )

    def _get_running_simulation_ids(self, running_simulations: List[dict]) -> Set[str]:
        """Extracts IDs from running simulations."""
        return {simulation.sim_id for simulation in running_simulations}

    def _filter_events_by_running_simulations(
        self, 
        events_by_simulation: Dict[str, List[dict]], 
        running_sim_ids: Set[str]
    ) -> List[dict]:
        """Filters events to only include those from running simulations."""
        return [
            event 
            for sim_id, events in events_by_simulation.items() 
            for event in events 
            if sim_id in running_sim_ids
        ]

    async def _fetch_events(self) -> List[dict]:
        """
        Fetches events and filters them to only include those from running simulations.
        Returns an empty list if no valid events are found.
        """
        # Get new events
        events = await super()._fetch_events()
        if not events:
            return []

        # Group events by simulation
        events_by_simulation = await self._group_events_by_simulation(events)

        # Get running simulations
        running_simulations = await self._get_running_simulations(list(events_by_simulation.keys()))
        if not running_simulations:
            self.logger.info("No running simulations to publish events for.")
            return []

        # Filter events to only include those from running simulations
        running_sim_ids = self._get_running_simulation_ids(running_simulations)
        filtered_events = self._filter_events_by_running_simulations(
            events_by_simulation, 
            running_sim_ids
        )

        if not filtered_events:
            self.logger.info("No events from running simulations to publish.")
            return []

        return filtered_events
