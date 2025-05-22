
from app.utils.logger import LoggerManager
import asyncio
from datetime import datetime
from app.models.topolgy_simulation_models import SimulationMetaData, TopologyStatusEnum, TopologySimulation
from app.db.events_db import EventsDB
from app.core.validators.links_validators import LinksValidators
from app.models.statuses_enums import LinkStatusEnum
from app.models.events_models import LinkEvent
from app.db.topolgies_simulations_db import TopologiesSimulationsDB

class LinkBusinessLogic:
    def __init__(self, db):
        self.logger = LoggerManager.get_logger('links_bl')
        self.events_db = EventsDB(db)
        self.topologies_simulations_db = TopologiesSimulationsDB(db)
        self.validator_bl = LinksValidators(self.logger)

    async def run_link(self, link_event: LinkEvent, is_last_try: bool):
        self.logger.info(f"Running link {link_event.after.id} for simulation {link_event.sim_id}")
        
        is_operation_failed = False
        try:
            if self.validator_bl.run_pre_link_validator(link_event.after) is False:
                self.logger.error(f"Link {link_event.after.id} failed pre-validation")
                return
                        
            await asyncio.sleep(link_event.after.latency)

            if self.validator_bl.run_post_link_validator(link_event.after) is False:
                self.logger.error(f"Link {link_event.after.id} failed post-validation")
                return

            #update link status
            link_event.after.status = LinkStatusEnum.done
            await self.events_db.update_event(link_event.id, link_event)
            
            simulation = await self.topologies_simulations_db.get_simulation(link_event.sim_id)
        except Exception as e:
            self.logger.error(f"Error running link for simulation {link_event.sim_id}: {e}")
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
    async def handle_simulation_completion(self, simulation: TopologySimulation, meta_data: SimulationMetaData):
        if self.validator_bl.calculate_if_completed(simulation, meta_data):
            #packet_loss_percent - failed only if it's above this percent
            simulation.status = TopologyStatusEnum.done if meta_data.failed_links == 0 else TopologyStatusEnum.failed
            meta_data.end_time = meta_data.current_time
            self.logger.info(f"Simulation {simulation.sim_id} completed\nMeta data: {meta_data.model_dump()}")
            await self.simulation_db.update(simulation.sim_id, simulation)
    