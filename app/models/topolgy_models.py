from pydantic import BaseModel
from typing import Optional, List
from app.models.statuses_enums import  LinkStatusEnum
from datetime import datetime
from bson.objectid import ObjectId
from pydantic import Field
from typing import Literal
class Link(BaseModel):
    """
    Represents a network link between two nodes in the topology.
    Fields:
        - from_node: Source node name (aliased from 'from')
        - to_node: Destination node name (aliased from 'to')
        - latency: Link latency in seconds
    """
    id: Optional[str] = Field(None, alias="_id")
    from_node: str 
    to_node: str
    latency: int

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

class Topology(BaseModel):
    """
    Represents the network topology for a simulation.
    Fields:
        - nodes: List of node names
        - links: List of Link objects defining connections between nodes
    """
    id: Optional[str] = Field(None, alias="_id")
    nodes: List[str]
    links: List[Link]
    config: Optional[Config] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

