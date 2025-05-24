from app.db.topolgies_simulations_db import TopologiesSimulationsDB
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
        
    async def run_simulation(self, simulation_event: SimulationEvent):
        """
        Run a specific topology simulation.

        Args:
            simulation_id (str): The ID of the simulation to be run.
        """
        self.logger.info(f"Starting run of simulation with ID: {simulation_event.after.sim_id}")
        try:
            if self.validator_bl.run_pre_simulation_validators(simulation_event.after) is False:
                self.logger.error(f"Simulation {simulation_event.after.sim_id} failed pre-validation")
                return
                
            #update simulation
            simulation = await self.topologies_simulations_db.get_topology_simulation(simulation_event.after.sim_id)
            self.logger.set_level(simulation.topology.config.log_level)
            simulation_event.after.status = TopologyStatusEnum.running
            simulation_event.after.updated_at = datetime.now()
            simulation_event.after.simulation_time.start_time = datetime.now()
            simulation_event.after.row_version = simulation.row_version
            await self.topologies_simulations_db.update_simulation(simulation_event.after.sim_id, simulation_event.after)
            
            #store links events
            events = SimulationMapper.simulation_to_links_event(simulation_event.after)
            await self.events_db.store_events(events)
            
            #update simulation event
            await self.events_db.update_events_handled([simulation_event.event_id])
            
            self.logger.info(f"Successfully run {len(events)} links for simulation {simulation_event.after.sim_id}.")
        except Exception as e:
            self.logger.error(f"Error during run of {simulation_event.after.sim_id}simulation: {str(e)}")
            raise e
        
    def check_if_pause_is_open(self, simulation: TopologySimulation):
        return [pause for pause in simulation.simulation_time.pauses 
                      if pause.start_time is not None and pause.end_time is None]
        
    async def pause_simulation(self, simulation_event: SimulationEvent):
        """
        Pause a specific topology simulation.

        Args:
            simulation_id (str): The ID of the simulation to be paused.
        """ 
        self.logger.info(f"Pausing simulation with ID: {simulation_event.after.sim_id}")
        try:
            if self.check_if_pause_is_open(simulation_event.after   ) is not None:
                self.logger.warning(f"Simulation {simulation_event.after.sim_id} is already paused")
                return
            #update status
            simulation_event.after.status = TopologyStatusEnum.paused
            simulation_event.after.updated_at = datetime.now()
            simulation_event.after.simulation_time.pauses.append(PauseTime(start_time=datetime.now()))
            await self.topologies_simulations_db.update_simulation(simulation_event.after.sim_id, simulation_event.after)
            
            await self.events_db.update_events_handled([simulation_event.event_id])
            self.logger.info(f"Successfully paused simulation {simulation_event.after.sim_id}.")
        except Exception as e:
            self.logger.error(f"Error during pause of {simulation_event.after.sim_id} simulation: {str(e)}")
            raise e 
    
    def get_last_pause(self, simulation: TopologySimulation):
        matching_pauses = self.check_if_pause_is_open(simulation)
    
        if matching_pauses is not None and len(matching_pauses) > 1:
            self.logger.error(f"Found multiple unclosed pauses in simulation {simulation.sim_id}")
            raise ValueError(f"Found {len(matching_pauses)} unclosed pauses in simulation {simulation.sim_id}")
    
        return matching_pauses[0] if matching_pauses else None
    
    async def resume_simulation(self, simulation_event: SimulationEvent):
        """
        Resume a specific topology simulation.

        Args:
            simulation_id (str): The ID of the simulation to be resumed.
        """
        self.logger.info(f"Resuming simulation with ID: {simulation_event.after.sim_id}")
        try:
            last_pause = self.get_last_pause(simulation_event.after)
            if last_pause is None:
                self.logger.info(f"No unclosed pause found for simulation {simulation_event.after.sim_id}")
                return
            
            #update status
            simulation_event.after.status = TopologyStatusEnum.running
            simulation_event.after.updated_at = datetime.now()
            last_pause.end_time = datetime.now()
            last_pause.duration = last_pause.end_time - last_pause.start_time
            
            await self.topologies_simulations_db.update_simulation(simulation_event.after.sim_id, simulation_event.after)
            await self.events_db.update_events_handled([simulation_event.event_id])
            self.logger.info(f"Successfully resumed simulation {simulation_event.after.sim_id}.")
        except Exception as e:
            self.logger.error(f"Error during resume of {simulation_event.after.sim_id} simulation: {str(e)}")
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
        
    async def update_simulation_completed_status(self, simulation_event: SimulationEvent):
        try:
            if len(simulation_event.after.links_execution_state.failed_links) > 0:
                if self.links_validator.is_packet_loss_valid(simulation_event.after):
                    simulation_event.after.status = TopologyStatusEnum.done
                else:
                    simulation_event.after.status = TopologyStatusEnum.failed
            else:
                simulation_event.after.status = TopologyStatusEnum.done
            
            await self.calculate_simulation_time(simulation_event.after)
            await self.topologies_simulations_db.update_simulation(simulation_event.after.sim_id, simulation_event.after)
            await self.events_db.update_events_handled([simulation_event.event_id])
            self.logger.info(f"Simulation {simulation_event.after.sim_id} completed at: {simulation_event.after.simulation_time.end_time}")
        except Exception as e:
            self.logger.error(f"Error during update of simulation {simulation_event.after.sim_id} completed status: {str(e)}")
            raise e
            