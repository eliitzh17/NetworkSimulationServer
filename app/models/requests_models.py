from pydantic import BaseModel, Field
from app.models.topolgy_models import Topology, Config
from typing import Optional, List

class PaginationRequest(BaseModel):
    page: int = 1
    page_size: int = 10

class CursorPaginationRequest(BaseModel):
    cursor: Optional[str] = None  # MongoDB ObjectId as string
    page_size: int = 10
    with_total: bool = False

class SimulationRequest(BaseModel):
    """
    Request model for creating a new simulation.
    
    Fields:
        topology: Network topology containing nodes and links
            - nodes: List of node names (e.g., ["A", "B"])
            - links: List of links between nodes, each containing:
                - from_node: Source node name
                - to_node: Destination node name
                - latency: Link latency in seconds
        config: Optional simulation configuration
            - duration_sec: Duration of simulation in seconds (default: 30)
            - packet_loss_percent: Packet loss percentage (default: 0.0)
            - log_level: Logging level (default: "warning")
    
    Example:
        {
            "topology": {
                "nodes": ["A", "B"],
                "links": [
                    {
                        "from_node": "A",
                        "to_node": "B",
                        "latency": 2
                    }
                ]
            },
            "config": {
                "duration_sec": 60,
                "packet_loss_percent": 0.1,
                "log_level": "info"
            }
        }
    """
    topology: Topology = Field(
        ...,
        description="Network topology containing nodes and links",
        example={
            "nodes": ["A", "B"],
            "links": [
                {
                    "from_node": "A",
                    "to_node": "B",
                    "latency": 2
                }
            ]
        }
    )
    config: Optional[Config] = Field(
        None,
        description="Optional simulation configuration",
        example={
            "duration_sec": 60,
            "packet_loss_percent": 0.1,
            "log_level": "info"
        }
    )