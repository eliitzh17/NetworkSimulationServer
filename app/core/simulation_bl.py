from app.db.simulation_meta_data_db import SimulationMetaDataDB
from app.db.simulation_db import SimulationDB
from app.utils.logger import LoggerManager
from app.utils.simulation_utils import create_simulation_metadata
from app.models.simulation_models import Simulation, TopologyStatusEnum
from datetime import datetime
from app.rabbit_mq.publishers.simulations_publisher import SimulationsPublisher
from app.rabbit_mq.publishers.links_publisher import LinksPublisher
from app.models.simulation_models import LinkBusMessage
from app.core.validator_bl import ValidatorBusinessLogic

class SimulationBusinessLogic:
    def __init__(self, db, rabbitmq_client):
        self.simulation_db = SimulationDB(db)
        self.simulation_meta_data_db = SimulationMetaDataDB(db)
        self.logger = LoggerManager.get_logger('simulation_bl')
        self.validator_bl = ValidatorBusinessLogic(self.logger)
        self.rabbitmq_client = rabbitmq_client
        
    async def publish_new_simulation(self, simulation: Simulation):
        await self.store_new_simulation(simulation)
        simulations_publisher = SimulationsPublisher(self.rabbitmq_client)
        await simulations_publisher.publish_simulations_messages([simulation])

    #store simulation and meta data
    async def store_new_simulation(self, simulation: Simulation):
        meta_data = create_simulation_metadata(simulation.sim_id)
        simulation.meta_data_id = meta_data.id
        await self.simulation_db.store_simulation(simulation)
        await self.simulation_meta_data_db.store_meta_data(meta_data)

    #here we can receive the full object
    async def run_simulation(self, id):
        #fetch data
        simulation = await self.simulation_db.get_simulation(id)
        meta_data = await self.simulation_meta_data_db.get_by_sim_id(id)
        
        #pre validation
        self.validator_bl.time_validator_for_simulation(simulation)
        self.validator_bl.validate_all_link_nodes_exists(simulation)
        
        #update status
        simulation.status = TopologyStatusEnum.running
        await self.simulation_db.update(simulation.sim_id, simulation)
        
        #update time
        meta_data.start_time = datetime.now()
        meta_data.current_time = datetime.now()
        await self.simulation_meta_data_db.update(meta_data.id, meta_data)

        #run links
        links_publisher = LinksPublisher(self.rabbitmq_client)
        
        #mappr to link with sim_id
        links_body = [LinkBusMessage(sim_id=simulation.sim_id, link=link) for link in simulation.topology.links]
        await links_publisher.publish_run_links_messages(links_body)
        
    async def mark_simulation_as_completed(self, id):
        simulation = await self.simulation_db.get_simulation(id)
        
        if simulation.meta_data.failed_links > 0:
            simulation.status = TopologyStatusEnum.failed
        else:
            simulation.status = TopologyStatusEnum.done
            
        meta_data = await self.simulation_meta_data_db.get_by_sim_id(id)
        meta_data.end_time = datetime.now()
        meta_data.total_execution_time = meta_data.end_time - meta_data.start_time
        await self.simulation_meta_data_db.update(meta_data.id, meta_data)
        await self.simulation_db.update(simulation.sim_id, simulation)
        
    async def mark_simulation_as_paused(self, id):
        simulation = await self.simulation_db.get_simulation(id)
        simulation.status = TopologyStatusEnum.paused
        simulation.meta_data.current_time = datetime.now()
            
        meta_data = await self.simulation_meta_data_db.get_by_sim_id(id)
        meta_data.total_execution_time = meta_data.end_time - meta_data.start_time
        await self.simulation_meta_data_db.update(meta_data.id, meta_data.model_dump())
        await self.simulation_db.update(simulation.sim_id, simulation.model_dump())
        
    # async def 

