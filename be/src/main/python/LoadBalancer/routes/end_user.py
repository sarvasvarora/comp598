from fastapi import APIRouter
from ..env import *
from ..shared_resources import *
from ..models import *


router = APIRouter()


####################
# HEAVY JOB ENDPOINT
####################
@router.get("/heavy")
def heavy():
    pass


#####################
# MEDIUM JOB ENDPOINT
#####################
@router.get("/medium")
def medium():
    pass


####################
# LIGHT JOB ENDPOINT
####################
@router.get("/light")
def light():
    pass