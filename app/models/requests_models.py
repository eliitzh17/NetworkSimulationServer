from pydantic import BaseModel
from app.models.simulation_models import Topology, Config
from typing import Optional

class PaginationRequest(BaseModel):
    page: int = 1
    page_size: int = 10

class CursorPaginationRequest(BaseModel):
    cursor: Optional[str] = None  # MongoDB ObjectId as string
    page_size: int = 10
    with_total: bool = False

class SimulationRequest(BaseModel):
    topology: Topology
    config: Optional[Config] = None