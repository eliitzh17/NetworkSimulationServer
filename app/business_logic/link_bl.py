from app.utils.logger import LoggerManager
import asyncio
from datetime import datetime
from app.models.topolgy_simulation_models import TopologySimulation
from app.db.events_db import EventsDB
from app.business_logic.validators.links_validators import LinksValidators
from app.models.statuses_enums import LinkStatusEnum
from app.models.events_models import LinkEvent
from app.db.topologies_simulations_db import TopologiesSimulationsDB
from app.models.topolgy_simulation_models import LinkExecutionState

class LinkBusinessLogic:
    def __init__(self, db):
        self.logger = LoggerManager.get_logger('links_bl')
        self.events_db = EventsDB(db)
        self.topologies_simulations_db = TopologiesSimulationsDB(db)
        self.validator_bl = LinksValidators()

    async def _update_links_state(self, link_event: LinkEvent, simulation: TopologySimulation):
        """
        Update the final state of the link execution in a transaction.
        This ensures that both the event and simulation updates are atomic.
        """
        async with await self.events_db.db.client.start_session() as session:
            async with session.start_transaction():
                await self.events_db.update_events_handled([link_event.event_id], session=session)
                await self.topologies_simulations_db.update_simulation(link_event.sim_id, simulation, session=session)

    async def run_link(self, link_event: LinkEvent, is_last_retry: bool):
        if is_last_retry:
            self.logger.info(f"Running link {link_event.after.id} for simulation {link_event.sim_id} (last retry)")
        try:
            simulation = await self.topologies_simulations_db.get_topology_simulation(link_event.sim_id)
            if simulation is None:
                self.logger.error(f"Simulation {link_event.sim_id} not found")
                return

            if self.validator_bl.run_pre_link_validator(simulation, link_event.after) is False:
                self.logger.error(f"Link {link_event.after.id} failed pre-validation")
                return
            
            link_exec_state = self.validator_bl.get_not_processed_link(simulation, link_event.after)
            link_exec_state.start_time = datetime.now()
                        
            await asyncio.sleep(link_event.after.latency)

            simulation = await self.topologies_simulations_db.get_topology_simulation(link_event.sim_id)
            if self.validator_bl.run_post_simulation_Validator(simulation) is False:
                self.logger.error(f"Link {link_event.after.id} failed post-validation")
                return

            link_exec_state.status = LinkStatusEnum.done
        except Exception as e:
            self.logger.error(f"Error running link for simulation {link_event.sim_id}: {e}")
            link_exec_state = self.validator_bl.get_not_processed_link(simulation, link_event.after)
            link_exec_state.retry_count += 1
            if is_last_retry:
                link_exec_state.status = LinkStatusEnum.failed
            raise e
        finally:
            simulation, link_event = self.end_link_enrichment(simulation, link_event, link_exec_state)
            await self._update_links_state(link_event, simulation)

    def end_link_enrichment(self, simulation: TopologySimulation, link_event: LinkEvent, link_exec_state: LinkExecutionState):
        
        link_event.is_handled = True
        link_exec_state.end_time = datetime.now()
        
        if link_exec_state.status == LinkStatusEnum.failed:
            self.logger.error(f"Link of simulation {simulation.sim_id} failed")
            simulation.links_execution_state.add_link_state_to_failed(link_exec_state)
        else:
            self.logger.info(f"Link of simulation {simulation.sim_id} succeeded")
            simulation.links_execution_state.add_link_state_to_success(link_exec_state)
            
        return simulation, link_event
        

    