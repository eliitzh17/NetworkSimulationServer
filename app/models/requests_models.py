from pydantic import BaseModel
from app.models.simulation_models import Topology, Config
from typing import Optional

class SimulationRequest(BaseModel):
    topology: Topology
    config: Optional[Config] = None