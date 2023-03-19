from fastapi import APIRouter
from .env import *


router = APIRouter()


####################
# HEAVY JOB ENDPOINT
####################
@app.get("/heavy")
def heavy():
    pass


#####################
# MEDIUM JOB ENDPOINT
#####################
@app.get("/medium")
def medium():
    pass


####################
# LIGHT JOB ENDPOINT
####################
@app.get("/light")
def light():
    pass