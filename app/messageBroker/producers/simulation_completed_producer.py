from app.messageBroker.producers.base_producer import BaseProducer
from app.models.events_models import LinkEvent
from app.models.statuses_enums import EventType
from app.business_logic.topologies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.models.pageination_models import CursorPaginationRequest
from app.models.mapper import SimulationMapper
import asyncio
from app.models.topolgy_simulation_models import TopologySimulation
from typing import List, Set, Dict
from app.app_container import app_container
import traceback
from app.models.message_bus_models import OutboxPublisher
from app.db.topologies_simulations_db import TopologiesSimulationsDB
from app.models.events_models import SimulationEvent

class SimulationCompletedProducer(BaseProducer):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        super().__init__(rabbitmq_manager, exchange_name, db, app_container.config().SIMULATION_QUEUE)
        self.topologies_simulations_bl = TopologiesSimulationsBusinessLogic(db)
        self.db = db
        self.topologies_simulations_db = TopologiesSimulationsDB(db)    
        self.config = app_container.config()
        self._initialize_outbox_publisher()

    def _initialize_outbox_publisher(self):
        """Initialize the outbox publisher with simulation completion specific configuration."""
        self.outbox_publisher = OutboxPublisher(
            initial_delay=self.config.INITIAL_DELAY,
            max_retries=self.config.MAX_RETRIES,
            retry_delay=self.config.RETRY_DELAY,
            batch_size_events_query=self.config.PAGE_SIZE,
            max_messages_to_publish=self.config.MAX_SIMULATIONS_IN_PARALLEL_COMPLETED_PRODUCER
        )

    def _get_event_filter(self) -> dict:
        """Returns the filter for finding unhandled and unpublished simulation completion events."""
        return {
            "is_handled": True,
            "published": False,
            "event_type": EventType.LINK_RUN.value
        }

    async def _get_completed_simulations(self) -> List[TopologySimulation]:
        """Fetch completed simulations from the database."""
        return await self.topologies_simulations_bl.find_completed_simulations(
            CursorPaginationRequest(page=1, page_size=self.outbox_publisher.batch_size_events_query)
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
        # Return the newly created events
        return await self.events_db.find_events_by_filter({
            "$and": [
                {"event_type": EventType.LINK_COMPLETED.value},
                {"published": False}
            ]
        }, limit=self.outbox_publisher.batch_size_events_query)

    def _group_events_by_simulation(self, events: List[dict]) -> Dict[str, List[dict]]:
        """
        Groups events by their simulation ID.
        
        Args:
            events: List of events to group
            
        Returns:
            Dictionary where keys are simulation IDs and values are lists of events for that simulation
        """
        events_by_simulation = {}
        
        for event in events:
            sim_id = event.get('sim_id')
            if sim_id:
                if sim_id not in events_by_simulation:
                    events_by_simulation[sim_id] = []
                events_by_simulation[sim_id].append(event)
                
        return events_by_simulation

    async def _publish_and_update_events(self, events: List[LinkEvent], simulations_to_publish: List[SimulationEvent], routing_key: str) -> int:
        """
        Common method to publish events and update their status.
        Uses MongoDB transactions to ensure atomicity between publishing and updating.
        Returns the number of events that were successfully processed.
        """
        if not events:
            self.logger.info("No new events to publish.")
            return 0

        self.logger.info(f"Publishing {len(events)} events.")

        try:
            async with await self.db.client.start_session() as session:
                async with session.start_transaction():
                    # Update the original link events as published
                    event_ids = [event['_id'] for event in events if event.get('_id')]
                    updated_count = await self.events_db.update_events_published(event_ids, session=session)
                    
                    # Store simulation events with published=True to prevent double processing
                    for event in simulations_to_publish:
                        event.published = True
                    await self.events_db.store_events(simulations_to_publish, session=session)
                    
                    # Publish the messages
                    publish_events = [event.model_dump(by_alias=True) for event in simulations_to_publish]
                    await self._publish_messages(publish_events, routing_key=routing_key)
                    
                    self.logger.info(f"Published and marked {updated_count} events as handled.")
                    return updated_count
        except Exception as e:
            updated_count = await self.events_db.update_events_published(event_ids, is_published=False)
            self.logger.error(f"Failed to publish events to RabbitMQ: {e}")
            raise e

    async def run_outbox_producer(self):
        """
        Base implementation of the outbox producer loop.
        Handles fetching, publishing, and updating events with backpressure.
        """
        await asyncio.sleep(self.outbox_publisher.initial_delay)
        
        while True:
            try:
                # Apply backpressure
                await self.backpressure_manager.apply_backpressure()
                
                # Fetch events
                events = await self._fetch_events()
                if not events:
                    self.logger.info("No events to publish.")
                    await asyncio.sleep(20)
                    continue

                events_by_simulation = self._group_events_by_simulation(events)

                updated_simulations = []
                completed_simulations = []
                for simulation_id in events_by_simulation.keys():
                    simulation = await self.topologies_simulations_db.get_topology_simulation(simulation_id)
                    if simulation is None:
                        self.logger.error(f"Simulation {simulation_id} not found")
                        continue
                    new_completed_links = [event['after'] for event in events_by_simulation[simulation_id] if event.get('after')]
                    simulation.links_execution_state.move_links_to_processed(new_completed_links)      
                    if len(simulation.links_execution_state.not_processed_links) == 0:
                        completed_simulations.append(simulation)
                    else:
                        updated_simulations.append(simulation)
                completed_simulations_events = []
                updated_simulations_events = []
                
                if completed_simulations:
                    completed_simulations_events = SimulationMapper.simulations_to_events(
                        completed_simulations, 
                        EventType.SIMULATION_COMPLETED
                    )
                if updated_simulations:
                    updated_simulations_events = SimulationMapper.simulations_to_events(
                        updated_simulations, 
                        EventType.SIMULATION_UPDATED
                    )
                simulations_to_publish = completed_simulations_events + updated_simulations_events
                # Publish and update events
                updated_count = await self._publish_and_update_events(events, simulations_to_publish, self.routing_queue)
                await self._log_backpressure_stats(updated_count)

                await asyncio.sleep(20)

            except Exception as e:
                self.logger.error(f"Error in publish_new_events_batch: {e}\n{traceback.format_exc()}")
                raise e