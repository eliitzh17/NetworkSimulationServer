from app.db.simulation_meta_data_db import SimulationMetaDataDB
from app.db.simulation_db import SimulationDB
from app.utils.logger import LoggerManager
from app.utils.simulation_utils import create_simulation_metadata
from app.models.simulation_models import Simulation, TopologyStatusEnum
from datetime import datetime
from app.rabbit_mq.publishers.simulations_publisher import SimulationsPublisher
from app.rabbit_mq.publishers.links_publisher import LinksPublisher
from app.models.simulation_models import LinkBusMessage
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from config import get_config

class SimulationBusinessLogic:
    def __init__(self, db):
        self.simulation_db = SimulationDB(db)
        self.simulation_meta_data_db = SimulationMetaDataDB(db)
        self.logger = LoggerManager.get_logger('simulation_bl')
        
    async def publish_new_simulation(self, simulation: Simulation):
        await self.store_new_simulation(simulation)
        rabbit_mq_client = RabbitMQClient(get_config().RABBITMQ_URL)
        simulations_publisher = SimulationsPublisher(rabbit_mq_client)
        await simulations_publisher.publish_simulations_messages([simulation])

    async def store_new_simulation(self, simulation: Simulation):
        meta_data = create_simulation_metadata(simulation.sim_id)
        simulation.meta_data_id = meta_data.id
        await self.simulation_db.store_simulation(simulation)
        await self.simulation_meta_data_db.store_meta_data(meta_data)

    async def run_simulation(self, id):
        #fetch data
        simulation = await self.simulation_db.get_simulation(id)
        meta_data = await self.simulation_meta_data_db.get_by_sim_id(id)
        
        
        #update status
        simulation.status = TopologyStatusEnum.running
        await self.simulation_db.update(simulation.sim_id, simulation.model_dump())
        
        #update time
        meta_data.start_time = datetime.now()
        meta_data.current_time = datetime.now()
        await self.simulation_meta_data_db.update(meta_data.id, meta_data.model_dump())

        #run links
        rabbit_mq_client = RabbitMQClient(get_config().RABBITMQ_URL)
        links_publisher = LinksPublisher(rabbit_mq_client)
        links_body = [LinkBusMessage(sim_id=simulation.sim_id, link=link) for link in simulation.topology.links]
        await links_publisher.publish_links_messages(links_body)

