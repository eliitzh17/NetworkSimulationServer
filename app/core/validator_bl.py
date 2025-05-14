from app.models.simulation_models import Simulation, Link, SimulationMetaData, TopologyStatusEnum
import pandas as pd
from datetime import datetime
class ValidatorBusinessLogic:
    def __init__(self, logger):
        self.logger = logger
    
    #pre validation
    def node_exist(self, simulation: Simulation, node: str):
        if node not in simulation.topology.nodes:
            self.logger.error(f"Node not found: {node} in simulation {simulation.sim_id}")
            raise ValueError(f"Node {node} not found")
        
    def validate_all_link_nodes_exists(self, simulation: Simulation):
        for link in simulation.topology.links:
            self.validate_link_nodes_exist(simulation, link)

    def validate_link_nodes_exist(self, simulation: Simulation, link: Link):
        self.node_exist(simulation, link.from_node)
        self.node_exist(simulation, link.to_node)

    def time_validator_for_link(self, simulation: Simulation, meta_data: SimulationMetaData, link: Link):
        if link.latency > simulation.config.duration_sec:
            self.logger.error(f"Link latency is greater than simulation duration: {link.latency} > {simulation.config.duration_sec}")
            raise ValueError(f"Link latency is greater than simulation duration: {link.latency} > {simulation.config.duration_sec}")
        
        time_left_sec = simulation.config.duration_sec - pd.Timedelta(meta_data.current_time - meta_data.start_time).total_seconds()
    
        if time_left_sec < link.latency:
            self.logger.error(f"Time left for simulation ({time_left_sec}) is less than link latency ({link.latency})")
            raise ValueError(f"Time left for simulation ({time_left_sec}) is less than link latency ({link.latency})")
        
    def time_validator_for_simulation(self, simulation: Simulation):
        highest_latency = max(simulation.topology.links, key=lambda x: x.latency).latency
        
        if simulation.config.duration_sec < highest_latency:
            self.logger.error(f"Simulation duration is less than link latency: {simulation.config.duration_sec} < {highest_latency}")
            raise ValueError(f"Simulation duration is less than link latency: {simulation.config.duration_sec} < {highest_latency}")
        
    def is_simulation_in_valid_state(self, simulation: Simulation):
        if simulation.status is not TopologyStatusEnum.running and simulation.status is not TopologyStatusEnum.pending:
            self.logger.error(f"Simulation is not in valid state and it's current state is: {simulation.status}")
            raise ValueError(f"Simulation is not in valid state and it's current state is: {simulation.status}")
        
    #post validation
    #consider retry
    def validate_packet_loss_percent(self, simulation: Simulation, meta_data: SimulationMetaData):
        if meta_data.failed_links == 0 or meta_data.processed_links == 0:
            return
        
        current_packet_loss_percent = meta_data.failed_links / meta_data.processed_links
        if current_packet_loss_percent > simulation.config.packet_loss_percent:
            self.logger.error(f"Current packet loss percent is greater than threshold percent: {current_packet_loss_percent} > {simulation.config.packet_loss_percent}")
            raise ValueError(f"Current packet loss percent is greater than threshold percent: {current_packet_loss_percent} > {simulation.config.packet_loss_percent}")
        
    def validate_timeout(self, simulation: Simulation):
        if simulation.meta_data.current_time - simulation.meta_data.start_time > simulation.config.duration_sec:
            self.logger.error(f"Timeout exceeded: {simulation.meta_data.current_time - simulation.meta_data.start_time} > {simulation.config.duration_sec}")
            raise ValueError(f"Timeout exceeded: {simulation.meta_data.current_time - simulation.meta_data.start_time} > {simulation.config.duration_sec}")
    
    def calculate_if_completed(self, simulation: Simulation, meta_data: SimulationMetaData):
        if meta_data.processed_links == len(simulation.topology.links):
            return True
        return False
            


    
