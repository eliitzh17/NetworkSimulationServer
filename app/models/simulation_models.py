from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from app.models.statuses_enums import LinkStatusEnum, TopologyStatusEnum
from datetime import datetime
import uuid

class Link(BaseModel):
    """
    Represents a network link between two nodes in the topology.
    Fields:
        - from_node: Source node name (aliased from 'from')
        - to_node: Destination node name (aliased from 'to')
        - latency: Link latency in seconds
    """
    from_node: str 
    to_node: str
    latency: int
    
class LinkBusMessage(BaseModel):
    """
    Represents a network link between two nodes in the topology.
    Fields:
        - sim_id: Simulation id
        - link: Link object
    """
    sim_id: str
    link: Link

class Topology(BaseModel):
    """
    Represents the network topology for a simulation.
    Fields:
        - nodes: List of node names
        - links: List of Link objects defining connections between nodes
    """
    nodes: List[str]
    links: List[Link]

class Config(BaseModel):
    """
    Configuration for a simulation run.
    Fields:
        - duration_sec: Duration of the simulation in seconds (default: 30)
        - packet_loss_percent: Packet loss percentage (default: 0.0)
        - log_level: Logging level (default: 'warning')
    """
    duration_sec: int = 30
    packet_loss_percent: float = 0.0
    log_level: Literal["debug", "info", "warning", "error"] = "warning"
    
class SimulationMetaData(BaseModel):
    
    #identification
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))#let you db do it
    sim_id: str
    
    #time
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_time: Optional[datetime] = None#argue about it
    total_execution_time: int = 0
    
    #links
    processed_links: int = 0
    failed_links: int = 0
    success_links: int = 0
    
    #machine info
    os: str
    machine_id: str
    machine_name: str
    machine_ip: str
    machine_port: int

class Simulation(BaseModel):
    """
    Represents a simulation instance with its configuration, topology, and status.
    Fields:
        - sim_id: Unique simulation identifier
        - topology: Topology object
        - config: Config object
        - status: Current status of the simulation (StatusEnum)
        - retry_count: Number of retry attempts for failed operations
    """
    sim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topology: Topology
    config: Config
    status: Optional[TopologyStatusEnum] = TopologyStatusEnum.pending
    retry_count: int = 3
    meta_data_id: str = None
    # Optionally, you can add status_history: List[StatusEnum] = [] 
    
# class SimulationHistory(BaseModel):
#     id: str = Field(default_factory=lambda: str(uuid.uuid4()))
#     sim_id: str
#     status: TopologyStatusEnum
    

