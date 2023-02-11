from fastapi import FastAPI
from typing import Union
from pydantic import BaseModel
from typing import Optional, List
import socket

proxy_host = "10.140.17.114"
proxy_port = 8000
socket = socket.socket()

class Node(BaseModel):
    name: str
    pod_name: str
    cpu: Optional[int] = None
    memory: Optional[int] = None
    storage: Optional[int] = None

class ResourcePod(BaseModel):
    name: str
    nodes: Optional[List[str]] = None

class Job(BaseModel):
    jobId: int
    status: str
    path: str

pods = []
nodes = {}
jobQueue = []

app = FastAPI()

@app.get("/")
def read_root():
    return {"Resource Manager"}

@app.get("/init/")
def init():
    # Do all the setup here
    socket.connect((proxy_host, proxy_port))
    msg = "init"
    socket.send(msg.encode())
    
    # Should return the proxy response below
    return {"Initializing Setup"}

@app.get("/pods/")
def read_pods():
    return {"Pods": pods}


@app.post("/pods/")
def create_pod(pod: ResourcePod):
    # Make docker cmd call to create pod
    pods.append(pod)
    return pod

@app.delete("/pods/{pod_name}")
def delete_pod(pod_name: str):
    # Make docker cmd call to remove pod
    return {"pod": [f"delete pod {pod_name}\n"]}

@app.get("/nodes/")
def read_nodes():
    return {"Nodes": nodes}

@app.post("/nodes/")
def create_node(node: Node):
    # Make docker cmd call to create node
    nodes[node.name] = node.pod_name
    return node

@app.delete("/nodes/{node_name}")
def delete_node(node_name: str):
    # Make docker cmd call to remove pod
    nodes.pop(node_name)
    return {"node": [f"delete node {node_name}\n"]}

@app.get("/jobs/")
def read_jobs():
    return {"Jobs": jobQueue}

@app.post("/jobs/")
def create_job(job: Job):
    # Make docker cmd call to create node
    jobQueue.append(job)
    return job

@app.delete("/jobs/{job_id}")
def delete_node(job_id: int):
    # Make docker cmd call to remove pod
    jobQueue.pop(job_id)
    return {"job": [f"delete job {job_id}\n"]}

def connectThroughProxy():
    headers = "" # Should define the headers here
    try:
        s = socket.socket()
        s.connect((host,port))
        s.send(headers.encode('utf-8'))
        response = s.recv(3000)
        print (response)
        s.close()
    except socket.error as m:
       print (str(m))
       s.close() 