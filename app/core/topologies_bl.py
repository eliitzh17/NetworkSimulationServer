from app.db.toplogies_db import TopologiesDB
from typing import List
from app.core.validators.topolgy_validators import TopologiesValidators
from app.utils.logger import LoggerManager
from app.models.topolgy_simulation_models import TopologySimulation
from app.core.topolgies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.models.requests_models import SimulationRequest
from app.models.mapper import SimulationMapper
from bson import ObjectId

class TopologiesBL:
    def __init__(self, db):
        self.logger = LoggerManager.get_logger('topologies_bl')
        self.db = db
        self.topologies_db = TopologiesDB(db)
        self.topologies_simulations_bl = TopologiesSimulationsBusinessLogic(db)
        self.topolgies_validators = TopologiesValidators()
        
        
    async def trigger_simulation(self, simulations_requests: List[SimulationRequest], session=None):
        self.logger.info(f"Triggering simulation for {len(simulations_requests)} topologies")
        
        if len(simulations_requests) == 0:
            self.logger.error("No suitable topologies to simulate")
            return
        
        topologies = []
        for simulation_request in simulations_requests:
            if self.topolgies_validators.validate_topologies(simulation_request.topology) is False:
                self.logger.error(f"Invalid topologies: {simulation_request.topology}")
                continue
            topologies.append(simulation_request)
        
        full_topologies = await self.topologies_db.store_topologies(SimulationMapper.enrich_topologies(topologies), session=session)
        
        simulations = []
        for topology in full_topologies:
            simulation = TopologySimulation(
                topology=topology,
            )
            simulation.sim_id = str(ObjectId())
            simulations.append(simulation)
        sim_ids = await self.topologies_simulations_bl.create_topologies_simulations(simulations, session=session)
        self.logger.info(f"Successfully triggered simulation for {len(simulations)} topologies")
        return sim_ids
