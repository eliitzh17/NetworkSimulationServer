from app.bus_messages.publishers.base_publisher import BasePublisher
from app.models.statuses_enums import EventType
import os
from app.business_logic.topolgies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.models.pageination_models import CursorPaginationRequest
from app.models.mapper import SimulationMapper
import asyncio
from app.db.events_db import EventsDB
from app.models.topolgy_simulation_models import TopologySimulation
from typing import List

class SimulationCompletedPublisher(BasePublisher):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        self.topologies_simulations_bl = TopologiesSimulationsBusinessLogic(db)
        self.events_db = EventsDB(db)
        super().__init__(rabbitmq_manager, 'simulation_completed_publisher', exchange_name, db)
        
    async def filter_published_simulations(self, simulations: List[TopologySimulation]):
        sim_ids = [sim.sim_id for sim in simulations]
        existing_events = await self.events_db.find_events_by_filter({
            "event_type": EventType.SIMULATION_COMPLETED,
            "after._id": {"$in": sim_ids}
        }, limit=100)
        # Build a set of sim_ids that already have a completed event
        existing_sim_ids = set()
        for event in existing_events:
            after = event.get("after")
            if after and after.get("_id"):
                existing_sim_ids.add(after["_id"])
        # Filter out simulations whose sim_id is in existing_sim_ids
        return [sim for sim in simulations if sim.sim_id not in existing_sim_ids]
                
    async def run_outbox_publisher(self):
        while True:
            try:
                simulations = await self.topologies_simulations_bl.find_completed_simulations(CursorPaginationRequest(page=1, page_size=10))
                
                if not simulations:
                    await asyncio.sleep(10)
                    continue
              
                filtered_simulations = await self.filter_published_simulations(simulations)
                if not filtered_simulations:
                    await asyncio.sleep(10)
                    continue
                completed_simulations = SimulationMapper.simulations_to_events(filtered_simulations, EventType.SIMULATION_COMPLETED)
                await self.events_db.store_events(completed_simulations)
                await asyncio.sleep(10)
            except Exception as e:
                self.logger.error(f"Error in simulation completed publisher: {e}")
                await asyncio.sleep(10)
