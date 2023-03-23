from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from ..env import *
from ..shared_resources import *
from ..models import *


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

@router.post("/pods/{pod_id}")
def update_pod_status(pod_id: str, data: PodUpdateReq):
    data = jsonable_encoder(data)
    database.update_pod_status(pod_id, data['status'])
    pod = database.get_pod(pod_id)
    request_monitor.log_pod_status(pod['type'], pod['status'])
    return {"Successfully updated pod status"}


#################
# NODE ENDPOINTS
#################
@router.post("/nodes")
async def add_node(node: NodeReq):
    node = jsonable_encoder(node)
    database.add_node(node)
    pod = database.get_pod(node['podId'])
    request_monitor.log_num_nodes(pod['type'], len(pod['nodes']))
    return {"Successfully added node."}


@router.delete("/nodes/{node_id}")
async def delete_node(node_id: str):
    database.delete_node(node_id)
    pod = database.get_pod(node_id)
    request_monitor.log_num_nodes(pod['type'], len(pod['nodes']))
    return {"Successfully deleted node."}


@router.post("/nodes/{node_id}")
async def update_node(node_id: str, data: NodeUpdateReq):
    data = jsonable_encoder(data)
    database.update_node_status(node_id, data['status'])
    return {"Successfully updated node status."}