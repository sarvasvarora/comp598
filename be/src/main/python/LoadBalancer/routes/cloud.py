from fastapi import APIRouter
from .env import *
from .models import PodReq, NodeReq


router = APIRouter()


################
# POD ENDPOINTS
################
@router.post("/pod")
def add_pod(pod: PodReq):
    pass


@router.delete("/pod/{pod_id}")
def delete_pod():
    pass


@router.update("/pod/{pod_id}")
def update_pod():
    pass


#################
# NODE ENDPOINTS
#################
@router.post("/nodes")
def add_node(node: NodeReq):
    pass


@router.delete("/nodes/{node_id}")
def delete_node():
    pass


@router.update("/nodes/{node_id}")
def update_node():
    pass