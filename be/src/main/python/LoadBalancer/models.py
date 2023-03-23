from pydantic import BaseModel
from typing import Literal


class PodReq(BaseModel):
    name: str
    podId: str
    type: Literal['heavy', 'HEAVY', 'medium', 'MEDIUM', 'light', 'LIGHT']

class PodUpdateReq(BaseModel):
    status: Literal['active', 'ACTIVE', 'inactive', 'INACTIVE']

class NodeReq(BaseModel):
    name: str
    nodeId: str
    podId: str
    uri: str

class NodeUpdateReq(BaseModel):
    status: Literal['new', 'NEW', 'online', 'ONLINE']