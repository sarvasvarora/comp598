from pydantic import BaseModel
from typing import Optional, List


class Pod(BaseModel):
    name: str
    nodes: Optional[List[str]] = None

class Node(BaseModel):
    name: str
    podId: str
    cpu: Optional[int] = None
    memory: Optional[int] = None
    storage: Optional[int] = None

class Job(BaseModel):
    path: str