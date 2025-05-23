from pydantic import BaseModel, Field
from datetime import datetime
from app.models.statuses_enums import EventType
from typing import TypeVar, Generic, Optional
from app.models.topolgy_simulation_models import TopologySimulation
from app.models.topolgy_models import Link
T = TypeVar('T', bound=BaseModel)

class BaseEvent(BaseModel, Generic[T]):
    """
    Represents an event in the simulation.
    """
    event_id: Optional[str] = Field(None, alias="_id")
    event_type: EventType
    before: Optional[T] = None
    after: T
    is_handled: bool = False
    retry_count: int = 0
    published: bool = False
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
class SimulationEvent(BaseEvent[TopologySimulation]):
    pass

class LinkEvent(BaseEvent[Link]):
    sim_id: str