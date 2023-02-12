from fastapi import FastAPI
from typing import Union
from pydantic import BaseModel
from typing import Optional, List
import socket
from datetime import datetime
import json

proxy_host = "10.140.17.114"
proxy_port = 8000
socket = socket.socket()
defaultCluster = None
defaultPod = None
pods = {}   # key: pod_name      value: pod object
nodes = {}  # key: node_name     value: node object
jobQueue = []

class Cluster(BaseModel):
    name: str

class Node(BaseModel):
    name: str
    pod_name: str
    status: str = None
    cpu: Optional[int] = None
    memory: Optional[int] = None
    storage: Optional[int] = None

class ResourcePod(BaseModel):
    name: str
    nodes: Optional[List[Node]] = None
    cluster: Optional[Cluster] = None

class Job(BaseModel):
    jobId: int
    status: str
    path: str

app = FastAPI()

@app.get("/")
def read_root():
    return {"Resource Manager"}

@app.get("/init/")
def init():
    # Initialize default cluster and pod
    global defaultCluster
    global defaultPod
    defaultCluster = Cluster(name='default')
    defaultPod = ResourcePod(name='default', nodes=[], cluster=defaultCluster)
    pods['default'] = defaultPod
    
    # The init command on the proxy side will create default nodes under the default pod
    try:
        socket.connect((proxy_host, proxy_port))
        message2send = {'cmd': 'init'}
        socket.send(json.dumps(message2send, default=str).encode('utf-8'))
        resp = socket.recv(8192).decode('utf-8')
        print(json.loads(resp))
    except:
        return "Failed to connect to the proxy server"
    
    # Should return the proxy response below
    return "Initialization Done"

@app.get("/pods/")
def read_pods():
    return pods

@app.post("/pods/")
def create_pod(pod: ResourcePod):
    # NOTE The functionality of registering pods is not used in A1.
    # Verify pod_name uniqueness
    if pod.name in pods:
        return f"A pod with {pod.name} already exists"
    global defaultCluster
    pod.cluster = defaultCluster
    pods[pod.name] = pod
    return f"Successfully created {pods[pod.name]}"

@app.delete("/pods/{pod_name}")
def delete_pod(pod_name: str):
    # Verify if pod can be deleted
    if pod_name == 'default':
        return "You cannot delete the default pod"
    if not pod_name in pods:
        return f"A pod named {pod_name} does not exist"
    if pods[pod_name].nodes:
        return f"Cannot delete pod {pod_name} as there are nodes registered to it"
 
    pods.pop(pod_name)
    return f"Successfully deleted pod {pod_name}"

@app.get("/nodes/")
def read_nodes():
    return nodes

@app.post("/nodes/")
def create_node(node: Node):
    if node.pod_name in pods:
        # TODO Add support for varrying size of containers
        message2send = {'cmd': 'node register', 'node_name': node.name , 'pod_name': node.pod_name}
        socket.send(json.dumps(message2send, default=str).encode('utf-8'))
        resp = json.loads(socket.recv(8192).decode('utf-8'))
        print(resp)
        node.status = 'idle'
        nodes[node.name] = node

        # Check if there is anything to be assigned to the node
        if jobQueue:
            # This function will update the jobs, and node status + making the docker call
            assignJobToNode(jobQueue.pop(0), node)
        
        return node
    else:
        return f"Error. A pod with id {node.pod_name} does not exists"

@app.delete("/nodes/{node_name}")
def delete_node(node_name: str):
    if node_name in nodes:
        node = nodes[node_name]
        if node.status and node.status == "idle":
            message2send = {'cmd': 'node rm', 'node_name': node.name , 'pod_name': node.pod_name}
            socket.send(json.dumps(message2send, default=str).encode('utf-8'))
            resp = json.loads(socket.recv(8192).decode('utf-8'))
            print(resp)

            parent_pod = pods[node.pod_name]
            removeNodesFromPodList([node.name],parent_pod)
            nodes.pop(node_name)

        else:
            return f"Node {node_name} is not idle at the moment and cannot be deleted"
    else:
        return f"A node named {node_name} does not exist"

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

def getPodByName(pod_name):
    for p in pods:
        if p.name == pod_name:
            return p
    return None
    
def assignJobToNode(job, node):
    pass

def removeNodesFromPodList(nodes_to_remove, pod):
    pod.nodes =  [ node
            for node in pod.nodes
            if node.name not in names_to_remove]