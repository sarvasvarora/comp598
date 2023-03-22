from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from ..env import *
from ..shared_resources import *
from ..models import PodReq, NodeReq, NodeUpdateReq


router = APIRouter()


################
# POD ENDPOINTS
################
@router.post("/pods")
def add_pod(pod: PodReq):
    pod = jsonable_encoder(pod)
    database.add_pod(pod)
    return {"Successfully added pod."}


@router.delete("/pods/{pod_id}")
def delete_pod():
    pass


#################
# NODE ENDPOINTS
#################
@router.post("/nodes")
def add_node(node: NodeReq):
    try:
        node = jsonable_encoder(node)
        database.add_node(node)
        return {"Successfully added node."}
    except Exception as e:
        print(str(r))


@router.delete("/nodes/{node_id}")
def delete_node(node_id: str):
    database.delete_node(node_id)
    return {"Successfully deleted node."}


@router.post("/nodes/{node_id}")
def update_node(node_id: str, data: NodeUpdateReq):
    data = jsonable_encoder(data)
    database.update_node_status(node_id, data['status'])
    return {"Successfully updated node status."}