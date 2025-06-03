from app.models.topolgy_simulation_models import TopologySimulation
from app.models.requests_models import SimulationRequest
from app.models.events_models import SimulationEvent, EventType
from typing import List
from app.models.events_models import LinkEvent
from bson import ObjectId
from app.models.topolgy_models import Topology, Config
from app.business_logic.exceptions import MapperError
from app.models.topolgy_simulation_models import LinkExecutionState
from app.models.topolgy_models import Link

class SimulationMapper:
    @staticmethod
    def enrich_topology(request: SimulationRequest) -> Topology:
        try:
            request.topology.config = request.topology.config if request.topology.config else request.config if request.config else Config(30, 0.0, "warning")
            request.topology.id = str(ObjectId()) if request.topology.id is None else request.topology.id
            for link in request.topology.links:
                link.id = str(ObjectId()) if link.id is None else link.id
            return request.topology
        except Exception as e:
            raise MapperError(f"Failed to enrich topology: {str(e)}") from e
    
    @staticmethod
    def simulations_to_events(simulations: List[TopologySimulation], event_type: EventType) -> List[SimulationEvent]:
        try:
            events = []
            for simulation in simulations:
                event = SimulationEvent(
                    event_type=event_type,
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


    @staticmethod
    def map_links_to_link_execution_state(links: List[Link]):
        link_execution_states = []
        for link in links:
            link_execution_state = LinkExecutionState()
            link_execution_state.link_id = link.id
            link_execution_states.append(link_execution_state)
        return link_execution_states