from enum import Enum


class NodeStatus(Enum):
    NEW = "new"
    ONLINE = "online"


class PodType(Enum):
    HEAVY = "heavy"
    MEDIUM = "medium"
    LIGHT = "light"

class PodStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"