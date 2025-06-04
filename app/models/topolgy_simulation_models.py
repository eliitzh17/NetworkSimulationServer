from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.models.topolgy_models import Topology
from app.models.statuses_enums import TopologyStatusEnum
from typing import List
from datetime import datetime
from app.models.topolgy_models import Link



class TopolgyLinksExecutionState(BaseModel):
    not_processed_links: List[Link] = []
    processed_links: List[Link] = []
    
    def move_links_to_processed(self, links: List[Link]):
        for link in links:
            link_id = link.get('_id')
            link_to_move = next((l for l in self.not_processed_links if l.id == link_id), None)
            if link_to_move:
                self.not_processed_links.remove(link_to_move)
                self.processed_links.append(link)
    
    def move_links_to_not_processed(self, links: List[Link]):
        for link in links:
            link_id = link.get('_id')
            link_to_move = next((l for l in self.processed_links if l.get('_id') == link_id), None)
            if link_to_move:
                self.processed_links.remove(link_to_move)
                self.not_processed_links.append(link)
    
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

