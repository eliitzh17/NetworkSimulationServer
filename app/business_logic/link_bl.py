
from app.utils.logger import LoggerManager
import asyncio
from datetime import datetime
from app.models.topolgy_simulation_models import TopologyStatusEnum, TopologySimulation
from app.db.events_db import EventsDB
from app.business_logic.validators.links_validators import LinksValidators
from app.models.statuses_enums import LinkStatusEnum
from app.models.events_models import LinkEvent
from app.db.topolgies_simulations_db import TopologiesSimulationsDB

class LinkBusinessLogic:
    def __init__(self, db):
        self.logger = LoggerManager.get_logger('links_bl')
        self.events_db = EventsDB(db)
        self.topologies_simulations_db = TopologiesSimulationsDB(db)
        self.validator_bl = LinksValidators()

    async def run_link(self, link_event: LinkEvent):
        self.logger.info(f"Running link {link_event.after.id} for simulation {link_event.sim_id}")
        
        try:
            simulation = await self.topologies_simulations_db.get_topology_simulation(link_event.sim_id)
            if simulation is None:
                self.logger.error(f"Simulation {link_event.sim_id} not found")
                return
            
            if self.validator_bl.run_pre_link_validator(simulation, link_event.after) is False:
                self.logger.error(f"Link {link_event.after.id} failed pre-validation")
                return
                        
            await asyncio.sleep(link_event.after.latency)

            if self.validator_bl.run_post_link_validator(simulation) is False:
                self.logger.error(f"Link {link_event.after.id} failed post-validation")
                return

            #update link status
            link_event.after.status = LinkStatusEnum.done
            link_event.is_handled = True
            await self.events_db.update_event(link_event.event_id, link_event)
            

            # await self.post_link_execution_actions(simulation)
        except Exception as e:
            self.logger.error(f"Error running link for simulation {link_event.sim_id}: {e}")
            raise e

        
    async def post_link_execution_actions(self, simulation: TopologySimulation, link_event: LinkEvent):
        
        #update meta data
        simulation.links_execution_state.processed_links += 1
        if link_event.after.status == LinkStatusEnum.failed:
            self.logger.error(f"Link of simulation {simulation.sim_id} failed")
            simulation.links_execution_state.failed_links += 1
        else:
            self.logger.info(f"Link of simulation {simulation.sim_id} succeeded")
            simulation.links_execution_state.success_links += 1
        simulation.links_execution_state.current_time = datetime.now()
        # meta_data.total_execution_time = meta_data.current_time - meta_data.start_time #TODO: calculate 
        
        await self.handle_simulation_completion(simulation)
        await self.topologies_simulations_db.update_simulations([(simulation.sim_id, simulation)])
        
        #use here in saga pattern, option 1 - lock, option 2 - saga pattern
    async def handle_simulation_completion(self, simulation: TopologySimulation):
        if self.validator_bl.calculate_if_completed(simulation, simulation.links_execution_state):
            #packet_loss_percent - failed only if it's above this percent
            simulation.status = TopologyStatusEnum.done if simulation.links_execution_state.failed_links == 0 else TopologyStatusEnum.failed
            simulation.end_time = simulation.links_execution_state.current_time
            self.logger.info(f"Simulation {simulation.sim_id} completed\nMeta data: {simulation.links_execution_state.model_dump()}")
            await self.topologies_simulations_db.update_simulations([(simulation.sim_id, simulation)])
    