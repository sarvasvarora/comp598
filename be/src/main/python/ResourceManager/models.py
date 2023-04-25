from fastapi import UploadFile
from pydantic import BaseModel
from typing import Optional, List
import json


class ClusterReq(BaseModel):
    name: str

class PodReq(BaseModel):
    name: str
    clusterId: Optional[str] = None

class NodeReq(BaseModel):
    name: str
    podId: Optional[str] = None
    cpu: Optional[int] = None
    memory: Optional[int] = None
    storage: Optional[int] = None

class JobReq(BaseModel):
    filename: str

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value

class PodElasticityRange(BaseModel):
    podId: str
    lower_size: int
    upper_size: int