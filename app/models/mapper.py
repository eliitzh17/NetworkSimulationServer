from app.models.topolgy_simulation_models import TopologySimulation
from app.models.requests_models import SimulationRequest
from app.models.events_models import SimulationEvent, EventType
from typing import List
from app.models.events_models import LinkEvent
from bson import ObjectId
from app.models.topolgy_models import Topology, Config
from app.core.exceptions import MapperError
class SimulationMapper:
    @staticmethod
    def enrich_topologies(requests: List[SimulationRequest]) -> List[Topology]:
        
        try:
            topologies = []
            for req in requests:
                req.topology.config = req.config or Config(30, 0.0, "warning")
                req.topology.id = str(ObjectId())
                for link in req.topology.links:
                    link.id = str(ObjectId())
                topologies.append(req.topology)
            return topologies
        except Exception as e:
            raise MapperError(f"Failed to enrich topologies: {str(e)}") from e
    
    @staticmethod
    def simulations_to_events(simulations: List[TopologySimulation]) -> List[SimulationEvent]:
        try:
            events = []
            for simulation in simulations:
                event = SimulationEvent(
                    event_type=EventType.SIMULATION_CREATED,
                    before=None,
                    after=simulation
                )
                event.event_id = str(ObjectId())
                events.append(event)
            return events
        except Exception as e:
            raise MapperError(f"Failed to map simulations to events: {str(e)}") from e
    
    @staticmethod
    def simulation_to_links_event(simulation: TopologySimulation) -> List[LinkEvent]:
        try:
            events = []
            for link in simulation.topology.links:
                event = LinkEvent(
                    event_type=EventType.LINK_RUN,
                    before=None,
                    after=link,
                    sim_id=simulation.sim_id
                )
                event.event_id = str(ObjectId())
                events.append(event)
            return events
        except Exception as e:
            raise MapperError(f"Failed to map simulation to links events: {str(e)}") from e
