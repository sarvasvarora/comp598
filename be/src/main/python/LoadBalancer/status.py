from enum import Enum


class NodeStatus(Enum):
    NEW = "new"
    ONLINE = "online"


class PodStatus(Enum):
    HEAVY = "heavy"
    MEDIUM = "medium"
    LIGHT = "light"