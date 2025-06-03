from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.models.topolgy_models import Topology
from app.models.statuses_enums import TopologyStatusEnum
from typing import List
from datetime import datetime
from app.models.statuses_enums import LinkStatusEnum

class LinkExecutionState(BaseModel):    
    link_id: str = Field(None, alias="_id")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    status: Optional[LinkStatusEnum] = LinkStatusEnum.pending

class TopolgyLinksExecutionState(BaseModel):
    not_processed_links: List[LinkExecutionState] = []
    processed_links: List[LinkExecutionState] = []
    failed_links: List[LinkExecutionState] = []
    success_links: List[LinkExecutionState] = []
    
    def add_link_state_to_success(self, link_state: LinkExecutionState):
        link = next((l for l in self.not_processed_links if l.link_id == link_state.link_id), None)
        if link:
            self.not_processed_links.remove(link)
            self.processed_links.append(link_state)
            self.success_links.append(link_state)
    
    def add_link_state_to_failed(self, link_state: LinkExecutionState):
        link = next((l for l in self.not_processed_links if l.link_id == link_state.link_id), None)
        if link:
            self.not_processed_links.remove(link)
            self.processed_links.append(link_state)
            self.failed_links.append(link_state)
    
class PauseTime(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
class SimulationTime(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_execution_time: Optional[int] = None
    pauses: List[PauseTime] = []
    
    
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
    simulation_time: SimulationTime = SimulationTime()
    status: Optional[TopologyStatusEnum] = TopologyStatusEnum.pending    
    updated_at: datetime = None
    created_at: datetime = None

