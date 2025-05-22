from enum import Enum

class TopologyStatusEnum(str, Enum):
    """
    Enum representing the lifecycle status of a simulation.
    Values:
        - pending: accepted, not yet started
        - running: simulation is active
        - paused: simulation is paused (optional support)
        - stopped: simulation was manually stopped
        - done: simulation completed after running duration
        - failed: unrecoverable error or max retries reached
    """
    pending = "pending"
    running = "running"
    paused = "paused"  # Optional support
    stopped = "stopped"
    done = "done"
    failed = "failed"
    
class LinkStatusEnum(str, Enum):
    """
    Enum representing the lifecycle status of a link.
    Values:
        - pending: link is pending
        - running: link is running
        - done: link is done
        - failed: link is failed
    """
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
    
class EventType(str, Enum):
    """
    Represents the type of event in the simulation.
    """
    SIMULATION_CREATED = "topology_created"
    SIMULATION_UPDATED = "topology_updated"
    LINK_RUN = "topology_link_run"
    LINK_UPDATED = "topology_link_updated"
    SIMULATION_ENDED = "topology_simulation_ended"