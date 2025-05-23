from app.db.toplogies_db import TopologiesDB
from typing import List
from app.business_logic.validators.topolgy_validators import TopologiesValidators
from app.utils.logger import LoggerManager
from app.models.topolgy_simulation_models import TopologySimulation
from app.business_logic.topolgies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.models.requests_models import SimulationRequest
from app.models.mapper import SimulationMapper
from bson import ObjectId
import asyncio
class TopologiesBL:
    def __init__(self, db):
        self.logger = LoggerManager.get_logger('topologies_bl')
        self.db = db
        self.topologies_db = TopologiesDB(db)
        self.topologies_simulations_bl = TopologiesSimulationsBusinessLogic(db)
        self.topolgies_validators = TopologiesValidators()
        
    async def trigger_simulation(self, simulations_requests: List[SimulationRequest], session=None):
        self.logger.info(f"Triggering simulation for {len(simulations_requests)} topologies")
        if not simulations_requests:
            self.logger.error("No suitable topologies to simulate")
            return []

        exist_topologies, new_requests = await self._split_requests_to_existing_and_new(simulations_requests, session)
        new_topologies = self._validate_and_enrich_new_topologies(new_requests)
        if not new_topologies and not exist_topologies:
            self.logger.error("No suitable topologies to simulate")
            return []

        if new_topologies:
            exist_topologies.extend(await self._store_new_topologies(new_topologies, session))

        sim_ids = await self._create_simulations(exist_topologies, session)
        self.logger.info(f"Successfully triggered simulation for {len(exist_topologies)} topologies")
        return sim_ids

    async def _split_requests_to_existing_and_new(self, simulations_requests: List[SimulationRequest], session=None):
        exist_topologies = []
        new_requests = []
        # Parallelize DB existence checks
        tasks = [self.topologies_db.get_exist_topology(req, session) for req in simulations_requests]
        results = await asyncio.gather(*tasks)
        for req, exist_topology in zip(simulations_requests, results):
            if exist_topology:
                exist_topologies.append(exist_topology)
            else:
                new_requests.append(req)
        return exist_topologies, new_requests

    def _validate_and_enrich_new_topologies(self, new_requests: List[SimulationRequest]):
        new_topologies = []
        for simulation_request in new_requests:
            if self.topolgies_validators.validate_topologies(simulation_request) is False:
                self.logger.error(f"Invalid topologies: {simulation_request.topology}")
                continue
            new_topologies.append(SimulationMapper.enrich_topology(simulation_request))
        return new_topologies

    async def _store_new_topologies(self, new_topologies, session=None):
        return await self.topologies_db.store_topologies(new_topologies, session=session)

    async def _create_simulations(self, topologies, session=None):
        simulations = []
        for topology in topologies:
            simulation = TopologySimulation(topology=topology)
            simulation.sim_id = str(ObjectId())
            simulations.append(simulation)
        return await self.topologies_simulations_bl.create_topologies_simulations(simulations, session=session)
