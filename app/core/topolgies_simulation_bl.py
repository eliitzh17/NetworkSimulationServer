from app.db.topolgies_simulations_db import TopologiesSimulationsDB
from app.utils.logger import LoggerManager
from app.models.topolgy_simulation_models import TopologySimulation
from typing import List
from app.db.events_db import EventsDB
from app.models.mapper import SimulationMapper
from datetime import datetime
from app.models.statuses_enums import TopologyStatusEnum
from app.models.events_models import SimulationEvent
from app.core.validators.simulation_validators import SimulationValidators
class TopologiesSimulationsBusinessLogic:
    """
    Business logic layer for managing topology simulations and related events.
    Handles creation of topology simulations and logs relevant actions.
    """
    def __init__(self, db):
        self.logger = LoggerManager.get_logger('topologies_simulations_bl')
        self.topologies_simulations_db = TopologiesSimulationsDB(db)
        self.events_db = EventsDB(db)
        self.validator_bl = SimulationValidators(self.logger)

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
            events = SimulationMapper.simulations_to_events(topologies_simulations)
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
                
            #update status
            self.logger.set_level(simulation_event.after.topology.config.log_level)
            simulation_event.after.status = TopologyStatusEnum.running
            simulation_event.after.created_at = datetime.now()
            await self.topologies_simulations_db.update_simulations([(simulation_event.after.sim_id, simulation_event.after)])
            
            #store links events
            events = SimulationMapper.simulation_to_links_event(simulation_event.after)
            await self.events_db.store_events(events)
            
            #update simulation event
            simulation_event.is_handled = True
            await self.events_db.update_event(simulation_event.id, simulation_event)
            
            self.logger.info(f"Successfully run {len(events)} links for simulation {simulation_event.after.sim_id}.")
        except Exception as e:
            self.logger.error(f"Error during run of {simulation_event.after.sim_id}simulation: {str(e)}")
            raise e
        
    async def end_simulation(self, simulation_event: SimulationEvent):
        """
        End a specific topology simulation.

        Args:
            simulation_id (str): The ID of the simulation to be ended.
        """
        self.logger.info(f"Tearing down simulation with ID: {simulation_event.after.sim_id}")
        try:
            #update status
            simulation_event.after.status = self.validator_bl.get_end_simulation_status(simulation_event.after)
            await self.topologies_simulations_db.update_simulations([(simulation_event.after.sim_id, simulation_event.after)])
            
            self.logger.info(f"Successfully ended simulation {simulation_event.after.sim_id}.")
        except Exception as e:
            self.logger.error(f"Error during end of {simulation_event.after.sim_id} simulation: {str(e)}")
            raise e
        
    async def pause_simulation(self, simulation_event: SimulationEvent):
        """
        Pause a specific topology simulation.

        Args:
            simulation_id (str): The ID of the simulation to be paused.
        """ 
        self.logger.info(f"Pausing simulation with ID: {simulation_event.after.sim_id}")
        try:
            #update status
            simulation_event.after.status = TopologyStatusEnum.paused
            await self.topologies_simulations_db.update_simulations([(simulation_event.after.sim_id, simulation_event.after)])
            
            self.logger.info(f"Successfully paused simulation {simulation_event.after.sim_id}.")
        except Exception as e:
            self.logger.error(f"Error during pause of {simulation_event.after.sim_id} simulation: {str(e)}")
            raise e 
        
    async def resume_simulation(self, simulation_event: SimulationEvent):
        """
        Resume a specific topology simulation.

        Args:
            simulation_id (str): The ID of the simulation to be resumed.
        """
        self.logger.info(f"Resuming simulation with ID: {simulation_event.after.sim_id}")
        try:
            #update status
            simulation_event.after.status = TopologyStatusEnum.running
            await self.topologies_simulations_db.update_simulations([(simulation_event.after.sim_id, simulation_event.after)])
            
            self.logger.info(f"Successfully resumed simulation {simulation_event.after.sim_id}.")
        except Exception as e:
            self.logger.error(f"Error during resume of {simulation_event.after.sim_id} simulation: {str(e)}")
            raise e

