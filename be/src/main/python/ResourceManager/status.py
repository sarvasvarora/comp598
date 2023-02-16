from enum import Enum


class NodeStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"

class JobStatus(Enum):
    REGISTERED = "registered"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"