from fastapi import UploadFile
from pydantic import BaseModel
from typing import Optional, List
import json


class Cluster(BaseModel):
    name: str

class Pod(BaseModel):
    name: str
    clusterId: Optional[str] = None

class Node(BaseModel):
    name: str
    podId: str
    cpu: Optional[int] = None
    memory: Optional[int] = None
    storage: Optional[int] = None

class Job(BaseModel):
    filename: str

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value