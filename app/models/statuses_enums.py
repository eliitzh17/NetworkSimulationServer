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
        - new: link is new
        - active: link is active
        - closed: link is closed
        - failed: link is failed
    """
    new = "new"
    active = "active"
    closed = "closed"
    failed = "failed"