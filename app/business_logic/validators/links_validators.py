"""
Validators for network link operations within a simulation topology.

This module provides validation logic for network links, including node existence, link timing, and packet loss constraints.
A logger instance must be provided to the LinksValidators class for logging warnings and errors during validation.
"""
from app.models.topolgy_models import Link
from app.models.statuses_enums import TopologyStatusEnum
from app.models.topolgy_simulation_models import TopologySimulation
from app.utils.logger import LoggerManager
from app.models.statuses_enums import LinkStatusEnum

class LinksValidators:
    """
    Provides validation methods for network links in a simulation topology.

    Args:
        logger: Logger instance for logging validation warnings and errors. Should implement standard logging methods (info, warning, error, etc.).
    """
    def __init__(self):
        """
        Initialize the LinksValidators with a logger.

        Args:
            logger: Logger instance for logging validation messages.
        """
        self.logger = LoggerManager.get_logger('links_validators')
        
    def calculate_time_left_for_simulation(self, simulation: TopologySimulation):
        """
        Calculate the remaining time for the simulation.

        Args:
            simulation (TopologySimulation): The simulation object.
        Returns:
            float: Time left in seconds.
        """
        time_left = simulation.topology.config.duration_sec - (simulation.meta_data.current_time - simulation.meta_data.start_time).total_seconds()
        self.logger.info(f"Calculated time left for simulation {simulation.sim_id}: {time_left} seconds")
        return time_left
    
    def validate_node_exist_in_topology(self, simulation: TopologySimulation, node: str):
        """
        Check if a node exists in the simulation topology.

        Args:
            simulation (TopologySimulation): The simulation object.
            node (str): Node name to check.
        Returns:
            bool: True if node exists, False otherwise (logs a warning).
        """
        if node not in simulation.topology.nodes:
            self.logger.warning(f"Node {node} not found in topology of simulation {simulation.sim_id}")
            return False
        self.logger.info(f"Node {node} exists in topology for simulation {simulation.sim_id}")
        return True
    
    def validate_link_nodes_exist_in_topology(self, simulation: TopologySimulation, link: Link):
        """
        Check if both nodes of a link exist in the simulation topology.

        Args:
            simulation (TopologySimulation): The simulation object.
            link (Link): The link to validate.
        Returns:
            bool: True if both nodes exist, False otherwise.
        """
        if not self.validate_node_exist_in_topology(simulation, link.to_node):
            return False
        if not self.validate_node_exist_in_topology(simulation, link.from_node):
            return False
        self.logger.info(f"Both nodes for link {link.id} exist in topology for simulation {simulation.sim_id}")
        return True

    def is_simulation_in_valid_state(self, simulation: TopologySimulation):
        """
        Check if the simulation is in a valid running state.

        Args:
            simulation (TopologySimulation): The simulation object.
        Returns:
            bool: True if simulation is running, False otherwise (logs a warning).
        """
        if simulation.status is not TopologyStatusEnum.running and simulation.status:
            self.logger.warning(f"Simulation {simulation.sim_id} is not in valid state and it's current state is: {simulation.status}")
            return False
        self.logger.info(f"Simulation {simulation.sim_id} is in a valid running state")
        return True
    
    def is_link_latecny_valid_in_simulation(self, simulation: TopologySimulation, link: Link):
        """
        Check if the link's latency does not exceed the simulation duration.

        Args:
            simulation (TopologySimulation): The simulation object.
            link (Link): The link to validate.
        Returns:
            bool: True if latency is valid, False otherwise (logs a warning).
        """
        if link.latency > simulation.topology.config.duration_sec:
            self.logger.warning(f"Link {link.id} latency is greater than simulation duration")
            return False
        self.logger.info(f"Link {link.id} latency {link.latency} is valid for simulation {simulation.sim_id}")
        return True
    
    def is_link_will_within_simulation(self, simulation: TopologySimulation, link: Link):
        """
        Check if the link's latency does not exceed the time left in the simulation.

        Args:
            simulation (TopologySimulation): The simulation object.
            link (Link): The link to validate.
        Returns:
            bool: True if latency is within the time left, False otherwise (logs a warning).
        """
        if link.latency > self.calculate_time_left_for_simulation(simulation):
            self.logger.warning(f"Link {link.id} latency is greater than time left for simulation")
            return False
        self.logger.info(f"Link {link.id} latency is within time left for simulation {simulation.sim_id}")
        return True
    
    def get_not_processed_link(self, simulation: TopologySimulation, current_link: Link):
        if simulation.links_execution_state is None or simulation.links_execution_state.not_processed_links is None:
            return None
        not_processed_link = next((link for link in simulation.links_execution_state.not_processed_links 
            if link.id == current_link.id),
            None
        )
        return not_processed_link
    
    def get_link(self, simulation: TopologySimulation, current_link: Link):
        processed_link = next((link for link in simulation.topology.links 
            if link.id == current_link.id),
            None
        )
        return processed_link
    
    
    def run_pre_link_validator(self, simulation: TopologySimulation, link: Link):
        """
        Run all pre-link validation checks (node existence, simulation state, link timing).

        Args:
            simulation (TopologySimulation): The simulation object.
            link (Link): The link to validate.
        Returns:
            bool: True if all checks pass, False otherwise.
        """
        node_exists = self.validate_link_nodes_exist_in_topology(simulation, link)
        simulation_state = self.is_simulation_in_valid_state(simulation)
        link_time_valid = self.is_link_latecny_valid_in_simulation(simulation, link)
        link_in_not_processed_links = self.get_not_processed_link(simulation, link) is not None
        result = node_exists and simulation_state and link_time_valid and link_in_not_processed_links
        self.logger.info(f"Pre-link validation {'passed' if result else 'failed'} for link {link.id} in simulation {simulation.sim_id}")
        return result

    def count_failed_links(self, simulation: TopologySimulation):
        return len([link for link in simulation.links_execution_state.processed_links if link.execution_state.status == LinkStatusEnum.failed])

    def is_packet_loss_valid(self, simulation: TopologySimulation):
        """
        Validate that the current packet loss percent does not exceed the configured threshold.

        Args:
            simulation (TopologySimulation): The simulation object.
        Returns:
            bool: True if packet loss percent is within the threshold, False otherwise (logs a warning).
        """
        failed_links_count = self.count_failed_links(simulation)
        processed_links_count = len(simulation.links_execution_state.processed_links)
        
        if failed_links_count == 0 or processed_links_count == 0:
            return True
        
        current_packet_loss_percent = failed_links_count / processed_links_count
        if current_packet_loss_percent > simulation.topology.config.packet_loss_percent:
            self.logger.warning(f"Current packet loss percent is greater than threshold percent: {current_packet_loss_percent} > {simulation.topology.config.packet_loss_percent}")
            return False
        self.logger.info(f"Packet loss percent validated for simulation {simulation.sim_id}: {current_packet_loss_percent}")
        return True
    
    def is_simulation_running(self, simulation: TopologySimulation):
        if simulation.status != TopologyStatusEnum.running:
            self.logger.warning(f"Simulation {simulation.sim_id} is not running")
            return False
        self.logger.info(f"Simulation {simulation.sim_id} is running")
        return True

    def run_post_simulation_Validator(self, simulation: TopologySimulation):
        """
        Run post-link validation checks (e.g., packet loss percent).

        Args:
            simulation (TopologySimulation): The simulation object.
        """
        packet_loss_valid = self.is_packet_loss_valid(simulation)
        simulation_running = self.is_simulation_running(simulation)
        self.logger.info(f"Post-link validation {'passed' if packet_loss_valid and simulation_running else 'failed'} for simulation {simulation.sim_id}")
        return packet_loss_valid and simulation_running
