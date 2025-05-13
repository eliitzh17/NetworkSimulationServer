from app.models.simulation_models import Simulation, Topology, Config
from app.models.requests_models import SimulationRequest
import uuid
from pydantic import Field

class SimulationMapper:
    @staticmethod
    def request_to_simulation(request: SimulationRequest) -> Simulation:
        return Simulation(
            topology=request.topology,
            config=request.config,
        ) 