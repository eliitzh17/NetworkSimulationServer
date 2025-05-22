from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.models.topolgy_models import Topology
from app.models.statuses_enums import TopologyStatusEnum
from typing import List
from datetime import datetime

class TopolgyLinksExecutionState(BaseModel):
    not_processed_links: List[str] = []
    processed_links: List[str] = []
    failed_links: List[str] = []
    success_links: List[str] = []
    
    def move_link_to_success(self, link_id: str):
        self.not_processed_links.remove(link_id)
        self.processed_links.append(link_id)
        self.success_links.append(link_id)
    
    def move_link_to_failed(self, link_id: str):
        self.not_processed_links.remove(link_id)
        self.processed_links.append(link_id)
        self.failed_links.append(link_id)
        
    
class TopologySimulation(BaseModel):
    """
    Represents a order instance with its configuration, topology, and status.
    Fields:
        - sim_id: Unique simulation identifier
        - topology: Topology object
        - config: Config object
        - row_version: Version of the simulation
        - links_execution_state: Execution state of the links
        - status: Current status of the simulation (StatusEnum)
        - retry_count: Number of retry attempts for failed operations
    """
    sim_id: str = Field(None, alias="_id")
    topology: Topology
    row_version: int = 1
    links_execution_state: TopolgyLinksExecutionState = TopolgyLinksExecutionState()
    status: Optional[TopologyStatusEnum] = TopologyStatusEnum.pending    
    updated_at: datetime = None
    created_at: datetime = None

