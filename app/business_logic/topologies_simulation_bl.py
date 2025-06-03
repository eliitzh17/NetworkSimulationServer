from app.db.topologies_simulations_db import TopologiesSimulationsDB
from app.utils.logger import LoggerManager
from app.models.topolgy_simulation_models import TopologySimulation
from typing import List
from app.db.events_db import EventsDB
from app.models.mapper import SimulationMapper
from datetime import datetime
from app.models.statuses_enums import TopologyStatusEnum, LinkStatusEnum
from app.models.events_models import SimulationEvent
from app.models.statuses_enums import EventType
from app.business_logic.validators.simulation_validators import SimulationValidators
from app.models.pageination_models import CursorPaginationRequest
from app.models.topolgy_simulation_models import LinkExecutionState, PauseTime
from app.business_logic.validators.links_validators import LinksValidators
from app.utils.logger import LoguruLogger

class TopologiesSimulationsBusinessLogic:
    """
    Business logic layer for managing topology simulations and related events.
    Handles creation of topology simulations and logs relevant actions.
    """
    def __init__(self, db):
        self.logger: LoguruLogger = LoggerManager.get_logger('topologies_simulations_bl')
        self.topologies_simulations_db = TopologiesSimulationsDB(db)
        self.events_db = EventsDB(db)
        self.validator_bl = SimulationValidators(self.logger)
        self.links_validator = LinksValidators()

    async def create_topologies_simulations(self, topologies_simulations: List[TopologySimulation], session=None):
        """
        Create new topology simulations and store corresponding events.

        Args:
            topologies_simulations (List[TopologySimulation]): List of topology simulation objects to be created.
        """
        self.logger.info(f"Starting creation of {len(topologies_simulations)} topology simulations.")
        try:
            topologies_simulations = await self.topologies_simulations_db.store_topologies_simulations(topologies_simulations, session=session)
            self.logger.info("Successfully stored topology simulations in the database.")
            events = SimulationMapper.simulations_to_events(topologies_simulations, EventType.SIMULATION_CREATED)
            self.logger.debug(f"Mapped {len(events)} simulations to events.")
            await self.events_db.store_events(events, session=session)
            self.logger.info("Successfully stored simulation events in the database.")
            return [simulation.sim_id for simulation in topologies_simulations]
        except Exception as e:
            self.logger.error(f"Error during creation of topology simulations: {str(e)}")
            raise
        
    async def run_simulation(self, simulation_event: SimulationEvent, session=None):
        """
        Run a specific topology simulation.

        Args:
            simulation_event: The simulation event to process
            session: MongoDB session for transaction support
        """
        self.logger.info(f"Starting run of simulation with ID: {simulation_event.after.sim_id}")
        try:
            if self.validator_bl.run_pre_simulation_validators(simulation_event.after) is False:
                self.logger.error(f"Simulation {simulation_event.after.sim_id} failed pre-validation")
                return
                
            #update simulation
            simulation = await self.topologies_simulations_db.get_topology_simulation(simulation_event.after.sim_id, session=session)
            if simulation.row_version != simulation_event.after.row_version:
                self.logger.error(f"Simulation {simulation_event.after.sim_id} has been updated since the event was created")
                raise Exception(f"Simulation {simulation_event.after.sim_id} has been updated since the event was created")
            
            self.logger.set_level(simulation.topology.config.log_level)
            simulation_event.after.status = TopologyStatusEnum.running
            simulation_event.after.updated_at = datetime.now()
            simulation_event.after.simulation_time.start_time = datetime.now()
            await self.topologies_simulations_db.update_simulation(simulation_event.after.sim_id, simulation_event.after, session=session)
            
            #store links events
            events = SimulationMapper.simulation_to_links_event(simulation_event.after)
            await self.events_db.store_events(events, session=session)
            
            await self.events_db.update_events_handled([simulation_event.event_id], session=session)

            self.logger.info(f"Successfully run {len(events)} links for simulation {simulation_event.after.sim_id}.")
        except Exception as e:
            self.logger.error(f"Error during run of {simulation_event.after.sim_id}simulation: {str(e)}")
            raise e

    async def find_completed_simulations(self, cursor_pagination_request: CursorPaginationRequest) -> List[TopologySimulation]:
        link_statuses = [LinkStatusEnum.done, LinkStatusEnum.failed]
        simulations = await self.topologies_simulations_db.get_simulations_by_statuses([TopologyStatusEnum.running], link_statuses, cursor_pagination_request)
        
        completed_simulations = []
        for simulation in simulations.items:
            if self.validator_bl.calculate_if_completed(simulation):
                completed_simulations.append(simulation)
                continue
            
        self.logger.info(f"Found {len(completed_simulations)} completed simulations")
        return completed_simulations

    def calculate_pause_time(self, simulation: TopologySimulation):
        return sum(pause.duration for pause in simulation.simulation_time.pauses if pause.duration is not None)
    
    async def calculate_simulation_time(self, simulation: TopologySimulation):
        
        if simulation.simulation_time.start_time is None:
            self.logger.warning(f"Simulation {simulation.sim_id} has no start time")
            return
        
        simulation.simulation_time.end_time = datetime.now() #take the last
        total_time = (simulation.simulation_time.end_time - simulation.simulation_time.start_time).total_seconds()
        pause_time = self.calculate_pause_time(simulation)
        simulation.simulation_time.total_execution_time = int(total_time - pause_time)
        
    async def update_simulation_completed_status(self, simulation_event: SimulationEvent, session=None):
        """
        Update the status of a completed simulation.

        Args:
            simulation_event: The simulation event to process
            session: MongoDB session for transaction support
        """
        try:
            if len(simulation_event.after.links_execution_state.failed_links) > 0:
                if self.links_validator.is_packet_loss_valid(simulation_event.after):
                    simulation_event.after.status = TopologyStatusEnum.done
                else:
                    simulation_event.after.status = TopologyStatusEnum.failed
            else:
                simulation_event.after.status = TopologyStatusEnum.done
            
            await self.calculate_simulation_time(simulation_event.after)
            await self.topologies_simulations_db.update_simulation(simulation_event.after.sim_id, simulation_event.after, session=session)
            await self.events_db.update_events_handled([simulation_event.event_id], session=session)
            self.logger.info(f"Simulation {simulation_event.after.sim_id} completed at: {simulation_event.after.simulation_time.end_time}")
        except Exception as e:
            self.logger.error(f"Error during update of simulation {simulation_event.after.sim_id} completed status: {str(e)}")
            raise e