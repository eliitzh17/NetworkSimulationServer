from app.db.simulation_db import SimulationDB
from app.db.simulation_meta_data_db import SimulationMetaDataDB
from app.utils.logger import LoggerManager
from app.models.simulation_models import Simulation, SimulationMetaData, Link
import pandas as pd
import asyncio


class LinkBusinessLogic:
    def __init__(self, db):
        self.simulation_db = SimulationDB(db)
        self.simulation_meta_data_repo = SimulationMetaDataDB(db)
        self.logger = LoggerManager.get_logger('link_bl')

    async def run_link(self, simulation_id, link: Link):
        self.logger.info(f"Running link for simulation {simulation_id}")
        
        #fetch data
        simulation = await self.simulation_db.get_simulation(simulation_id)        
        meta_data = await self.simulation_meta_data_repo.get_by_sim_id(simulation_id)
        
        #validation
        await self.nodes_validator(simulation, link)
        await self.time_validator(simulation, meta_data, link)
        
        #wait for link latency
        await asyncio.sleep(link.latency)        

    async def nodes_validator(self, simulation: Simulation, link: Link):
        if simulation.topology.nodes.count(link.from_node) == 0:
            self.logger.error(f"Node not found: {link.from_node} in simulation {simulation.sim_id}")
            raise ValueError(f"Node {link.from_node} not found")

        if simulation.topology.nodes.count(link.to_node) == 0:
            self.logger.error(f"Node not found: {link.to_node} in simulation {simulation.sim_id}")
            raise ValueError(f"Node {link.to_node} not found")


    async def time_validator(self, simulation: Simulation, meta_data: SimulationMetaData, link: Link):
        
        if pd.Timedelta(link.latency).total_seconds() > simulation.config.duration_sec:
            self.logger.error(f"Link latency is greater than simulation duration: {link.latency} > {simulation.config.duration_sec}")
            raise ValueError(f"Link latency is greater than simulation duration: {link.latency} > {simulation.config.duration_sec}")
        
        time_left_sec = simulation.config.duration_sec - pd.Timedelta(meta_data.current_time - meta_data.start_time).total_seconds()
    
        if time_left_sec < pd.Timedelta(link.latency).total_seconds():
            self.logger.error(f"Time left for simulation ({time_left_sec}) is less than link latency ({link.latency})")
            raise ValueError(f"Time left for simulation ({time_left_sec}) is less than link latency ({link.latency})")
    


