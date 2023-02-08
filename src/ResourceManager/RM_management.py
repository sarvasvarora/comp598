from fastapi import FastAPI
from typing import Union
from pydantic import BaseModel
from typing import Optional, List

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