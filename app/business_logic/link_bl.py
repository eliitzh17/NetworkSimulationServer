from app.utils.logger import LoggerManager
import asyncio
from datetime import datetime
from app.models.topolgy_simulation_models import TopologySimulation
from app.db.events_db import EventsDB
from app.business_logic.validators.links_validators import LinksValidators
from app.models.statuses_enums import LinkStatusEnum
from app.models.events_models import LinkEvent
from app.db.topologies_simulations_db import TopologiesSimulationsDB
from app.models.topolgy_models import LinkExecutionState
from app.models.statuses_enums import EventType
from app.models.topolgy_models import Link
from bson.objectid import ObjectId
import copy
import json
class LinkBusinessLogic:
    def __init__(self, db):
        self.logger = LoggerManager.get_logger('links_bl')
        self.events_db = EventsDB(db)
        self.topologies_simulations_db = TopologiesSimulationsDB(db)
        self.validator_bl = LinksValidators()

    async def _link_completed_db_updates(self, current_event: LinkEvent, completed_link: Link):
        """
        Update the final state of the link execution in a transaction.
        This ensures that both the event and simulation updates are atomic.
        """
        async with await self.events_db.db.client.start_session() as session:
            async with session.start_transaction():
                await self.events_db.update_events_handled([current_event.event_id], session=session)
                completed_link_event = LinkEvent(
                    event_type=EventType.LINK_COMPLETED,
                    before=current_event.after,
                    after=completed_link,
                    sim_id=current_event.sim_id,
                    is_handled=True,
                    published=False,
                    published_at=datetime.now(),
                    retry_count=current_event.after.execution_state.retry_count
                )
                completed_link_event.event_id = str(ObjectId())
                await self.events_db.store_events([completed_link_event], session=session)

    async def run_link(self, current_event: LinkEvent, is_last_retry: bool):
        if is_last_retry:
            self.logger.info(f"Running link {current_event.after.id} for simulation {current_event.sim_id} (last retry)")
        
        error = ''
        completed_link = copy.deepcopy(current_event.after)
        try:

            simulation = await self.topologies_simulations_db.get_topology_simulation(current_event.sim_id)
            if simulation is None:
                self.logger.error(f"Simulation {current_event.sim_id} not found")
                return

            completed_link.execution_state = LinkExecutionState(
                status=LinkStatusEnum.running,
                start_time=datetime.now(),
                retry_count=current_event.after.execution_state.retry_count +1
            )

            if self.validator_bl.run_pre_link_validator(simulation, completed_link) is False:
                self.logger.error(f"Link {current_event.after.id} failed pre-validation")
                raise ValueError(f"Link {current_event.after.id} failed pre-validation")
                        
            await asyncio.sleep(completed_link.latency)

            simulation = await self.topologies_simulations_db.get_topology_simulation(current_event.sim_id)
            if self.validator_bl.run_post_simulation_Validator(simulation) is False:
                self.logger.error(f"Link {current_event.after.id} failed post-validation")
                raise ValueError(f"Link {current_event.after.id} failed post-validation")

            completed_link.execution_state.status = LinkStatusEnum.done
        except ValueError as e:
            self.logger.error(f"Error running link validations {current_event.event_id} event: {e}")
            completed_link.execution_state.status = LinkStatusEnum.failed
            error = str(e)
            raise e
        except Exception as e:
            self.logger.error(f"Error running link {current_event.after.id} for simulation {current_event.sim_id}: {e}")
            completed_link.execution_state.status = LinkStatusEnum.failed
            error = str(e)
            raise e
        finally:
            if completed_link.execution_state.status == LinkStatusEnum.done or (completed_link.execution_state.status == LinkStatusEnum.failed and is_last_retry):
                completed_link.execution_state.end_time = datetime.now()
                current_event.is_handled = True
                await self._link_completed_db_updates(current_event, completed_link)
            else:
                raise Exception(f"Link {current_event.after.id} failed to process: {error}")