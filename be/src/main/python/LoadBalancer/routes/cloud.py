from fastapi import APIRouter
from .env import *


router = APIRouter()


################
# POD ENDPOINTS
################
@router.post("/pod")
def add_pod():
    pass


@router.delete("/pod")
def delete_pod():
    pass


@router.update("/pod")
def update_pod():
    pass


#################
# NODE ENDPOINTS
#################
@router.post("/node")
def add_node():
    pass


@router.delete("/node")
def delete_node():
    pass


@router.update("/node")
def update_node():
    pass