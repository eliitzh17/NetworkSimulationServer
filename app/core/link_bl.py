from app.db.simulation_db import SimulationDB
from app.db.simulation_meta_data_db import SimulationMetaDataDB
from app.utils.logger import LoggerManager
from app.models.simulation_models import Link
import asyncio
from app.core.validator_bl import ValidatorBusinessLogic
from datetime import datetime
from app.models.simulation_models import SimulationMetaData, TopologyStatusEnum, Simulation
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from config import get_config
from app.rabbit_mq.publishers.post_run_publisher import PostLinkRunPublisher
class LinkBusinessLogic:
    def __init__(self, db):
        self.simulation_db = SimulationDB(db)
        self.simulation_metadata_db = SimulationMetaDataDB(db)
        self.logger = LoggerManager.get_logger('link_bl')
        self.validator_bl = ValidatorBusinessLogic(self.logger)

    async def run_link(self, simulation_id, link: Link, is_last_try: bool):
        self.logger.info(f"Running link for simulation {simulation_id}")
        is_operation_failed = False
        post_run_publisher = PostLinkRunPublisher(RabbitMQClient(get_config().RABBITMQ_URL))
        try:
            #fetch data
            simulation = await self.simulation_db.get_simulation(simulation_id)        
            meta_data = await self.simulation_metadata_db.get_by_sim_id(simulation_id)
            
            if simulation is None:
                raise ValueError(f"Simulation {simulation_id} not found")
            
            if meta_data is None:
                raise ValueError(f"Meta data for simulation {simulation_id} not found")
            
            #validation
            self.validator_bl.is_simulation_in_valid_state(simulation)
            self.validator_bl.validate_link_nodes_exist(simulation, link)
            self.validator_bl.time_validator_for_link(simulation, meta_data, link)
            self.validator_bl.validate_packet_loss_percent(simulation, meta_data)

            #wait for link latency
            await asyncio.sleep(link.latency)
            await post_run_publisher.publish_post_links_execution_messages(simulation_id, False)

        except Exception as e:
            self.logger.error(f"Error running link for simulation {simulation_id}: {e}")
            is_operation_failed = True
            raise e
        finally:
            if is_last_try and not is_operation_failed:
                await post_run_publisher.publish_post_links_execution_messages(simulation_id, False)
        
    async def post_link_execution_actions(self, simulation_id: str, is_failed: bool):
        simulation = await self.simulation_db.get_simulation(simulation_id)
        meta_data = await self.simulation_metadata_db.get_by_sim_id(simulation_id)
        
        #update meta data
        meta_data.processed_links += 1
        if is_failed:
            self.logger.error(f"Link of simulation {simulation_id} failed")
            meta_data.failed_links += 1
        else:
            self.logger.info(f"Link of simulation {simulation_id} succeeded")
            meta_data.success_links += 1
        meta_data.current_time = datetime.now()
        # meta_data.total_execution_time = meta_data.current_time - meta_data.start_time #TODO: calculate 
        
        await self.handle_simulation_completion(simulation, meta_data)
        await self.simulation_metadata_db.update(meta_data.id, meta_data)
        
        #use here in saga pattern, option 1 - lock, option 2 - saga pattern
    async def handle_simulation_completion(self, simulation: Simulation, meta_data: SimulationMetaData):
        if self.validator_bl.calculate_if_completed(simulation, meta_data):
            #packet_loss_percent - failed only if it's above this percent
            simulation.status = TopologyStatusEnum.done if meta_data.failed_links == 0 else TopologyStatusEnum.failed
            meta_data.end_time = meta_data.current_time
            self.logger.info(f"Simulation {simulation.sim_id} completed\nMeta data: {meta_data.model_dump()}")
            await self.simulation_db.update(simulation.sim_id, simulation)
    