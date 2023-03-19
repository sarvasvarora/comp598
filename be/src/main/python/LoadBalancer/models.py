from pydantic import BaseModel


class PodReq(BaseModel):
    name: str
    podId: str


class NodeReq(BaseModel):
    name: str
    nodeId: str
    podId: str
    uri: str