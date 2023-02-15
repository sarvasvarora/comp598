from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from typing import Union
from typing import Optional, List
import socket
import os
from .database import Database
from .models import *
from .status import *
from .env import *

# create a new socket
socket = socket.socket()

# initialize the in-memory database
database = Database()

# initialize the FastAPI app
app = FastAPI()


###############
# ROOT ENDPOINT
###############
@app.get("/")
async def read_root():
    return {"Hello, World!"}


#####################
# CLOUD INIT ENDPOINT
#####################
@app.get("/init/")
async def init():
    # Do all the setup here
    socket.connect((PROXY_HOST, PROXY_PORT))
    msg = "init"
    socket.send(msg.encode())
    
    # Should return the proxy response below
    return {"Initializing Setup"}

###############
# POD ENDPOINTS
##############
@app.post("/pods/")
async def create_pod(pod: Pod):
    # Make docker cmd call to create pod
    pod_id = database.add_pod(jsonable_encoder(pod))
    return {"podId": pod_id}

@app.get("/pods/")
async def read_pods():
    return {"Pods": database.get_pods()}

@app.get("/pods/{pod_id}")
async def read_pod(pod_id: str):
    return {"pod": database.get_pod(pod_id)}

@app.get("/pods/{pod_id}/nodes/")
async def read_pod_nodes(pod_id: str):
    pod = database.get_pod(pod_id)
    nodes = database.get_nodes()
    return {"Nodes": [nodes[node_id] for node_id in pod['nodes']]}

@app.delete("/pods/{pod_id}")
async def delete_pod(pod_id: str):
    # Make docker cmd call to remove pod
    pod = database.delete_pod(pod_id)
    return {"pod": pod}


################
# NODE ENDPOINTS
################
@app.post("/nodes/")
async def create_node(node: Node):
    # Make docker cmd call to create node
    node = jsonable_encoder(node)
    node['status'] = NodeStatus.IDLE
    node_id = database.add_node(node)
    return {"nodeId": node_id} if node_id else {"Unable to add node. Please specify a valid pod ID."}

@app.get("/nodes/")
async def read_nodes():
    return {"Nodes": database.get_nodes()}

@app.get("/nodes/{node_id}")
async def read_node(node_id: str):
    return {"node": database.get_node(node_id)}

@app.delete("/nodes/{node_id}")
async def delete_node(node_id: str):
    # Make docker cmd call to remove pod
    node = database.delete_node(node_id)
    return {"node": node}


##############
# JOB ENDPOINT
##############
@app.post("/jobs/")
async def create_job(job: Job):
    # Make docker cmd call to create node
    job = jsonable_encoder(job)
    job['status'] = JobStatus.REGISTERED
    job_id = database.add_job(job)
    return {"jobId": job_id}

@app.get("/jobs/")
async def read_jobs():
    return {"Jobs": database.get_jobs()}

@app.get("/jobs/{job_id}")
async def read_job(job_id: str):
    return {"job": database.get_job(job_id)}

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    # Make docker cmd call to remove pod
    job = database.delete_job(job_id)
    return {"job": job}


# def connectThroughProxy():
#     headers = "" # Should define the headers here
#     try:
#         s = socket.socket()
#         s.connect((PROXY_HOST, PROXY_PORT))
#         s.send(headers.encode('utf-8'))
#         response = s.recv(3000)
#         print (response)
#         s.close()
#     except socket.error as m:
#        print (str(m))
#        s.close()