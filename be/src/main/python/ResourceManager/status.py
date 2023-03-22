from enum import Enum

class PodStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"

class NodeStatus(Enum):
    NEW = "new"
    ONLINE = "online"

class JobStatus(Enum):
    REGISTERED = "registered"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"