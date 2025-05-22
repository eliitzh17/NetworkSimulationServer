from app.models.topolgy_models import Topology
from app.utils.logger import LoggerManager
from app.db.toplogies_db import TopologiesDB
from app.models.topolgy_models import Config
from app.models.requests_models import SimulationRequest
from app.utils.object_utils import get_fingerprint
class TopologiesValidators:
    def __init__(self):
        self.logger = LoggerManager.get_logger('topologies_validators')

    def validate_links_is_not_empty(self, topology: Topology):
        topology_links = topology.links
        if len(topology_links) == 0:
            self.logger.warning(f"Topology {topology.id} has no links")
            return False
        return True
    
    def validate_nodes_is_not_empty(self, topology: Topology):
        topology_nodes = topology.nodes
        if len(topology_nodes) == 0:
            self.logger.warning(f"Topology {topology.id} has no nodes")
            return False
        return True

    def validate_nodes_is_not_duplicate(self, topology: Topology):
        topology_nodes = topology.nodes
        seen = set()
        duplicates = set()
        for node in topology_nodes:
            if node in seen:
                duplicates.add(node)
        else:
            seen.add(node)
        if duplicates:
            self.logger.warning(f"Topology {topology.id} has duplicate nodes: {', '.join(duplicates)}")
            return False
        return True
    
    def validate_links_is_pointing_to_different_nodes(self, topology: Topology):
        topology_links = topology.links
        for link in topology_links:
            if link.from_node == link.to_node:
                self.logger.warning(f"Topology {topology.id} has a link that points to the same node")
                return False
        return True
    
    def validate_max_nodes_is_valid(self, topology: Topology):
        topology_nodes = topology.nodes
        if len(topology_nodes) > 100:
            self.logger.warning(f"Topology {topology.id} has more than 100 nodes")
            return False
        return True
    
    def validate_max_links_is_valid(self, topology: Topology):
        topology_links = topology.links
        if len(topology_links) > 100:
            self.logger.warning(f"Topology {topology.id} has more than 100 links")
            return False
        return True
    
    def validate_topologies(self, simulation_request: SimulationRequest):
        self.logger.info(f"Validating new topology...")
        is_links_not_empty = self.validate_links_is_not_empty(simulation_request.topology)
        is_nodes_not_empty = self.validate_nodes_is_not_empty(simulation_request.topology)
        is_nodes_not_duplicate = self.validate_nodes_is_not_duplicate(simulation_request.topology)
        result = is_links_not_empty and is_nodes_not_empty and is_nodes_not_duplicate
        self.logger.info(f"New topology validation {'passed' if result else 'failed'}")
        return result