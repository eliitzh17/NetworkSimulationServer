from app.models.topolgy_simulation_models import TopologySimulation, TopologyStatusEnum
from app.business_logic.validators.links_validators import LinksValidators

class SimulationValidators:
    def __init__(self, logger):
        self.logger = logger
        self.links_validator = LinksValidators()
    
    def time_validator_for_simulation(self, simulation: TopologySimulation):
        highest_latency = max(simulation.topology.links, key=lambda x: x.latency).latency
        
        if simulation.topology.config.duration_sec < highest_latency:
            self.logger.warning(f"Simulation duration is less than link latency: {simulation.topology.config.duration_sec} < {highest_latency}")
            return False
        return True
    
    def validate_all_link_nodes_exists(self, simulation: TopologySimulation):
        for link in simulation.topology.links:
            self.links_validator.validate_link_nodes_exist_in_topology(simulation, link)
            
    def get_end_simulation_status(self, simulation: TopologySimulation):
        if simulation.status == TopologyStatusEnum.done:
            return TopologyStatusEnum.done
        elif simulation.status == TopologyStatusEnum.failed:
            return TopologyStatusEnum.failed
        else:
            return TopologyStatusEnum.running
        
    def calculate_if_completed(self, simulation: TopologySimulation):
        total_links = len(simulation.topology.links)
        processed_links = len(simulation.links_execution_state.processed_links)
        not_processed_links = len(simulation.links_execution_state.not_processed_links)
        
        is_completed = processed_links == total_links and not_processed_links == 0
        
        if not is_completed:
            self.logger.info(f"Simulation {simulation.sim_id} is not completed: processed={processed_links}/{total_links}, not_processed={not_processed_links}")
        
        return is_completed
    
    def already_running(self, simulation: TopologySimulation):
        return simulation.status == TopologyStatusEnum.running

    def run_pre_simulation_validators(self, simulation: TopologySimulation):
        time_valid = self.time_validator_for_simulation(simulation)
        all_link_nodes_exist = self.validate_all_link_nodes_exists(simulation)
        already_running = self.already_running(simulation)
        return time_valid and all_link_nodes_exist and not already_running
    
        
    def run_post_simulation_validators(self, simulation: TopologySimulation):
        packet_loss_valid = self.links_validator.is_packet_loss_valid(simulation)
        self.logger.info(f"Post-simulation validation completed for simulation {simulation.sim_id}")
        return packet_loss_valid