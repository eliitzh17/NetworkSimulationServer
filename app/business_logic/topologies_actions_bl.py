from app.db.topologies_simulations_db import TopologiesSimulationsDB
from app.db.events_db import EventsDB
from app.models.statuses_enums import TopologyStatusEnum
from app.models.statuses_enums import EventType
from app.models.topolgy_simulation_models import TopologySimulation
from app.models.topolgy_simulation_models import PauseTime
from app.models.mapper import SimulationMapper
from datetime import datetime
from app.utils.logger import LoggerManager
class SimulationActionsBL:
    def __init__(self, db):
        self.logger = LoggerManager.get_logger("topologies_actions_bl")
        self.db = db
        self.topologies_simulations_db = TopologiesSimulationsDB(db)
        self.events_db = EventsDB(db)

    async def pause_simulation(self, simulation: TopologySimulation, session=None) -> str:
        """
        Pause a specific topology simulation.

        Args:
            simulation_event: The simulation event to process
            session: MongoDB session for transaction support
        """
        self.logger.info(f"Pausing simulation with ID: {simulation.sim_id}")
        try:
            simulation = await self.topologies_simulations_db.get_topology_simulation(simulation.sim_id, session=session)
            if simulation.status != TopologyStatusEnum.running:
                self.logger.warning(f"Simulation {simulation.sim_id} is not running")
                return "Simulation is not running"
            
            #update status
            simulation.status = TopologyStatusEnum.paused
            simulation.updated_at = datetime.now()
            simulation.simulation_time.pauses.append(PauseTime(start_time=datetime.now()))
            
            await self.topologies_simulations_db.update_simulation(simulation.sim_id, simulation, session=session)
            self.logger.info(f"Successfully paused simulation {simulation.sim_id}.")
            return "Simulation paused successfully"
        except Exception as e:
            self.logger.error(f"Error during pause of {simulation.sim_id} simulation: {str(e)}")
            raise e
            
    async def restart_simulation(self, simulation: TopologySimulation, session=None):
        try:
            if simulation.status == TopologyStatusEnum.running:
                self.logger.warning(f"Simulation {simulation.sim_id} is already running")
                return
            
            #update status
            simulation.status = TopologyStatusEnum.pending
            simulation.updated_at = datetime.now()

            #reset simulation time
            simulation.simulation_time.start_time = None
            simulation.simulation_time.end_time = None
            simulation.simulation_time.total_execution_time = 0
            simulation.simulation_time.pauses = []

            #reset links execution state
            simulation.links_execution_state.failed_links = []
            simulation.links_execution_state.success_links = []
            simulation.links_execution_state.processed_links = []
            simulation.links_execution_state.not_processed_links = SimulationMapper.map_links_to_link_execution_state(simulation.topology.links)

            await self.topologies_simulations_db.update_simulation(simulation.sim_id, simulation, session=session)

            self.logger.info(f"Successfully restarted simulation {simulation.sim_id}")
        except Exception as e:
            self.logger.error(f"Error during restart of {simulation.sim_id} simulation: {str(e)}")
            raise e 

    def get_open_pauses(self, simulation: TopologySimulation):
        return [pause for pause in simulation.simulation_time.pauses 
                      if pause.start_time is not None and pause.end_time is None]
    
    def get_last_pause(self, simulation: TopologySimulation):
        matching_pauses = self.get_open_pauses(simulation)
    
        if matching_pauses is not None and len(matching_pauses) > 1:
            self.logger.error(f"Found multiple unclosed pauses in simulation {simulation.sim_id}")
            raise ValueError(f"Found {len(matching_pauses)} unclosed pauses in simulation {simulation.sim_id}")
    
        return matching_pauses[0] if matching_pauses else None


    async def resume_simulation(self, simulation: TopologySimulation, session=None) -> str:
        """
        Resume a specific topology simulation.

        Args:
            simulation_event: The simulation event to process
            session: MongoDB session for transaction support
        """
        self.logger.info(f"Resuming simulation with ID: {simulation.sim_id}")
        try:
            last_pause = self.get_last_pause(simulation)
            if last_pause is None:
                self.logger.info(f"No unclosed pause found for simulation {simulation.sim_id}")
                return "No unclosed pause found for simulation"
            
            #update status
            simulation.status = TopologyStatusEnum.running
            simulation.updated_at = datetime.now()
            last_pause.end_time = datetime.now()
            last_pause.duration = (last_pause.end_time - last_pause.start_time).total_seconds()
            
            await self.topologies_simulations_db.update_simulation(simulation.sim_id, simulation, session=session)
            self.logger.info(f"Successfully resumed simulation {simulation.sim_id}.")
            return "Simulation resumed successfully"
        except Exception as e:
            self.logger.error(f"Error during resume of {simulation.sim_id} simulation: {str(e)}")
            raise e