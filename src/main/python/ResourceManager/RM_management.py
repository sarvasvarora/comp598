from fastapi import BackgroundTasks, FastAPI
from fastapi import File, UploadFile
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
job_id_tracker = 0
pods = {}           # key: pod_name      value: pod object
nodes = {}          # key: node_name     value: node object
jobs = {}           # key: job_id        value: job object
jobQueue = []       # Stores JobId of job objects that are waiting
idle_nodes = []     # Stores nodeName of idle nodes 
running_nodes = []  # Stores (nodeName, jobID) of running nodes and what job they are running

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
    file: UploadFile

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
    global idle_nodes
    if node.pod_name in pods:
        # TODO Add support for varrying size of containers
        message2send = {'cmd': 'node register', 'node_name': node.name , 'pod_name': node.pod_name}
        socket.send(json.dumps(message2send, default=str).encode('utf-8'))
        resp = json.loads(socket.recv(8192).decode('utf-8'))
        print(resp)
        
        if resp['status'] == 200:
            # Node registration was successfull 
            node.status = 'idle'
            nodes[node.name] = node
            idle_nodes.append(node.name)
            print(idle_nodes)

            # Check if there is anything to be assigned to the node
            if jobQueue:
                # This function will update the jobs, and node status + making the docker call
                assignJobToNode(jobs[jobQueue.pop(0)], node)
            
            return node
        else: 
            return f"An error occured while registering node {node.name} on RP"
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
            idle_nodes.remove(node.name)
            nodes.pop(node_name)

        else:
            return f"Node {node_name} is not idle at the moment and cannot be deleted"
    else:
        return f"A node named {node_name} does not exist"

@app.get("/jobs/")
def read_jobs():
    return jobs

@app.post("/jobs/")
async def launch_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    global idle_nodes
    global running_nodes
    try:
        contents = file.file.read()
        with open(file.filename, 'wb') as f:
            f.write(contents)
    except Exception:
        return {"message": "An error occurred uploading the file"}
    finally:
        file.file.close()
    
    # Create job object
    global job_id_tracker
    job_id_tracker += 1
    job = Job(jobId=job_id_tracker, status='Registered', file=file)
    jobs[job.jobId] = job

    n = getFirstAvailableNode()

    # If no idle node -> place the job in the queue
    if not n:
        jobQueue.append(job.jobId)
        print(f"No idle node at the moment. Placed the job in the waiting queue")
        # TODO Once the job is taken out of the jobqueue, notify the user!
    else:
        # Update the client on job dispatch and wait for the RP proxy in background
        background_tasks.add_task(processJobLaunch,n, job, file)
        return {"message": f"Successfully dispatched and completed job {job.jobId}"}

def processJobLaunch(node, job, file):
    global idle_nodes
    global running_nodes
    # Status updates 
    node.status = 'Running'
    job.status = 'Running'
    idle_nodes.remove(node.name)
    running_nodes.append((node.name, job.jobId)) 

    with open(file.filename, 'r') as f:
            data = f.read()

    message2send = {'cmd': 'job launch', 'node_name': node.name , 'job_id': job.jobId, 'file': data}
    socket.send(json.dumps(message2send, default=str).encode('utf-8'))
    resp = json.loads(socket.recv(8192).decode('utf-8'))
    print(resp)
    if resp['status'] == 200:
        node.status = 'idle'
        job.status = 'Completed'
        running_nodes.remove((node.name,job.jobId))
        idle_nodes.append(node.name)

@app.delete("/jobs/{job_id}")
def abort_job(job_id: int):
    if not job_id in jobs:
        return f"No job with id {job_id}"
    if jobs[job_id].status == 'Completed':
        return f"Cannot abort job {job_id} as it is already completed"
    if jobs[job_id].status == 'Registered':
        jobQueue.remove(job_id)
        return f"Aborted job {job_id} successfully"
    if jobs[job_id].status == 'Running':
        # TODO Should we send a signal to the docker container to drop the work?
        try:
            jobs[job_id].status == 'Aborted'
            node_name = ''
            for (n, j) in running_nodes:
                if j == job_id:
                    node_name = n
                    nodes[n].status = 'idle'
                    idle_nodes.append(n)
                    break
            running_nodes.remove((node_name,job_id))
            return f"Aborted job {job_id} successfully"
        except:
            return f"An error occured while aborting job {job_id}"


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

def getFirstAvailableNode():
    if not idle_nodes:
        return None
    else: 
        return nodes[idle_nodes[0]]