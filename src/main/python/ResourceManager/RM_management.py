from fastapi import BackgroundTasks, FastAPI
from fastapi import File, UploadFile
from typing import Union
from pydantic import BaseModel
from typing import Optional, List
import socket
from datetime import datetime
from threading import Thread
import json

proxy_host = "10.140.17.114"
proxy_port = 8000
socket = socket.socket()
defaultCluster = None
defaultPod = None
pod_id_tracker = 0
node_id_tracker = 0
job_id_tracker = 0
pods = {}           # key: pod_id     value: pod object
nodes = {}          # key: node_id     value: node object
jobs = {}           # key: job_id        value: job object
jobQueue = []       # Stores JobId of job objects that are waiting
idle_nodes = []     # Stores nodeId of idle nodes 

class Cluster(BaseModel):
    name: str

class Node(BaseModel):
    name: str
    pod_id: int
    id: Optional[int] = None
    status: str = None
    cpu: Optional[int] = None
    memory: Optional[int] = None
    storage: Optional[int] = None

class ResourcePod(BaseModel):
    name: str
    id: Optional[int] = None
    nodes: Optional[List[Node]] = None
    cluster: Optional[Cluster] = None

class Job(BaseModel):
    jobId: Optional[int] = None
    nodeId: Optional[int] = None
    status: Optional[str] = None 
    name: str # Equal to the filepath
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
    defaultPod = ResourcePod(name='default', id=0, nodes=[], cluster=defaultCluster)
    pods[0] = defaultPod
    
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
def get_pods():
    result = []
    for pid in pods:
        p = pods[pid]
        result.append({'pod_name': p.name, 'pod_id': p.id, '# of attached nodes': len(p.nodes)})
    return result

@app.post("/pods/")
def create_pod(pod: ResourcePod):
    # NOTE The functionality of registering pods is not used in A1.
    # Verify pod_name uniqueness
    for pid in pods:
        if pods[pid].name == pod.name:
            return f"A pod with {pod.name} already exists"
    global defaultCluster
    global pod_id_tracker
    pod_id_tracker += 1
    pod.cluster = defaultCluster
    pod.id = pod_id_tracker
    pod.nodes = []
    pods[pod.id] = pod
    return f"Successfully created {pods[pod.id]}"

@app.delete("/pods/{pod_name}")
def delete_pod(pod_name: str):
    # Verify if pod can be deleted
    if pod_name == 'default':
        return "You cannot delete the default pod"

    pid_to_be_deleted = -1

    for pid in pods:
        p = pods[pid]
        if p.name == pod_name:
            if p.nodes:
                return f"Cannot delete pod {pod_name} as there are nodes registered to it"
            else:
                pid_to_be_deleted = pid
                break

    if pid_to_be_deleted == -1:
        return f"A pod with name {pod_name} does not exist"
    else:
        pods.pop(pid_to_be_deleted)
        return f"Successfully deleted pod {pod_name}"

@app.get("/nodes/{pod_id}")
def get_nodes(pod_id: int):
    result = [] 
    # All nodes in the cloud
    if pod_id == -1:
        for nid in nodes: 
            n = nodes[nid]
            result.append({'Name': n.name, 'ID': n.id , 'Status': n.status})
    else:
        pod = pods[pod_id]
        for nid in pods.nodes:
            n = nodes[nid]
            result.append({'Name': n.name, 'ID': n.id , 'Status': n.status})
    return result

@app.post("/nodes/")
def create_node(node: Node):
    global idle_nodes
    if node.pod_id in pods:
        # TODO Add support for varrying size of containers
        n = getNodeByName(node.name)
        if n:
            return f"A node with name {node.name} already exists in the default pod"
        
        message2send = {'cmd': 'node register', 'node_name': node.name , 'pod_name': pods[node.pod_id].name}
        print(message2send)
        socket.send(json.dumps(message2send, default=str).encode('utf-8'))
        resp = json.loads(socket.recv(8192).decode('utf-8'))
        print(resp)
        
        if resp['status'] == 200:
            # Node registration was successfull
            global node_id_tracker
            node_id_tracker += 1
            node.id = node_id_tracker
            node.status = 'idle'
            nodes[node.id] = node
            pods[node.pod_id].nodes.append(node.id)

            idle_nodes.append(node.id)
            pending_job_id = checkForPendingJobs(node)
            if pending_job_id: 
                print(f'Pending job with id {pending_job_id} is now assigned to node {node.name}')
                return {'node': node, 'message': f'Pending job with id {pending_job_id} is now assigned to node {node.name}'}
            else:
                return {'node': node}
        else: 
            return f"An error occured while registering node {node.name} on RP"
    else:
        return f"Error. A pod with id {node.pod_id} does not exists"

@app.delete("/nodes/{node_name}")
def delete_node(node_name: str):
    node = getNodeByName(node_name)
    if node:
        if node.status and node.status == "idle":
            message2send = {'cmd': 'node rm', 'node_name': node.name , 'pod_name': pods[node.pod_id].name}
            socket.send(json.dumps(message2send, default=str).encode('utf-8'))
            resp = json.loads(socket.recv(8192).decode('utf-8'))
            print(resp)

            parent_pod = pods[node.pod_id]
            parent_pod.nodes.remove(node.id)
            idle_nodes.remove(node.id)
            nodes.pop(node.id)
        else:
            return f"Node {node_name} is not idle at the moment and cannot be deleted"
    else:
        return f"A node named {node_name} does not exist"

@app.get("/jobs/{node_id}")
def get_jobs(node_id: int):
    result = [] 
    # All nodes in the cloud
    if node_id == -1:
        for jid in jobs: 
            j = jobs[jid]
            result.append({'Name': j.name, 'ID': j.jobId , 'Node_ID': j.nodeId, 'Status': j.status})
    else:
        for jid in jobs:
            j = jobs[jid]
            if j.nodeId == node_id:
                result.append({'Name': j.name, 'ID': j.jobId , 'Node_ID': j.nodeId, 'Status': j.status})
    return result

@app.get("/logs/{job_id}")
def get_logs(job_id: int):
    if not job_id in jobs:
        return f"Error: Job_id {job_id} does not exist"
    else: 
        job = jobs[job_id]
        node = nodes[job.nodeId]

        message2send = {'cmd': 'job log', 'node_name': node.name , 'pod_name': pods[node.pod_id].name, 'job_id': job_id}
        socket.send(json.dumps(message2send, default=str).encode('utf-8'))
        resp = json.loads(socket.recv(8192).decode('utf-8'))
        print(resp)
        return resp['log']

@app.get("/nodeLogs/{node_id}")
def get_node_logs(node_id: int):
    if not node_id in nodes:
        return f"Error: Node_id {job_id} does not exist"
    else: 
        node = nodes[node_id]

        message2send = {'cmd': 'node log', 'node_name': node.name , 'pod_name': pods[node.pod_id].name}
        socket.send(json.dumps(message2send, default=str).encode('utf-8'))
        resp = json.loads(socket.recv(8192).decode('utf-8'))
        print(resp)
        return resp['log']

@app.post("/jobs/")
async def launch_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    global idle_nodes
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
    job = Job(jobId=job_id_tracker, name=file.filename , status='Registered', file=file)
    jobs[job.jobId] = job

    n = getFirstAvailableNode()

    # If no idle node -> place the job in the queue
    if not n:
        jobQueue.append(job.jobId)
        return {"message": f"No idle node at the moment. Placed the job in the waiting queue"}
    else:
        # Update the client on job dispatch and wait for the RP proxy in background
        job.nodeId = n.id
        background_tasks.add_task(processJobLaunch, n, job, file)
        return {"message": f"Successfully dispatched job {job.jobId}"}

def processJobLaunch(node, job, file):
    global idle_nodes
    # Status updates 
    node.status = 'Running'
    job.status = 'Running'
    idle_nodes.remove(node.id)

    with open(file.filename, 'r') as f:
            data = f.read()

    message2send = {'cmd': 'job launch', 'node_name': node.name , 'job_id': job.jobId, 'file': data}
    socket.send(json.dumps(message2send, default=str).encode('utf-8'))
    resp = json.loads(socket.recv(8192).decode('utf-8'))
    print(resp)
    if resp['status'] == 200:
        node.status = 'idle'
        job.status = 'Completed'
        idle_nodes.append(node.id)
        pending_job_id = checkForPendingJobs(node)
        if pending_job_id: 
            print(f'Pending job with id {pending_job_id} is now assigned to node {node.name}')

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
            node = nodes[jobs[job_id].nodeId]
            jobs[job_id].status = 'Aborted'
            node.status = 'idle'
            idle_nodes.append(node.id)

            pending_job_id = checkForPendingJobs(node)
            if pending_job_id: 
                print(f'Pending job with id {pending_job_id} is now assigned to node {node.name}')
                return f"Aborted job {job_id} successfully. Pending job with id {pending_job_id} is now assigned to node {node.name}"
            else:
                return f"Aborted job {job_id} successfully"
        except:
            return f"An error occured while aborting job {job_id}"

def getFirstAvailableNode():
    if not idle_nodes:
        return None
    else: 
        return nodes[idle_nodes[0]]

def getNodeByName(node_name):
    for nid in nodes:
        n = nodes[nid]
        if n.name == node_name:
            return n
    return None

def checkForPendingJobs(node):
    # If there is any job waiting, assign the job to the free node
    if jobQueue:
        job = jobs[jobQueue.pop(0)]
        job.nodeId = node.id
        Thread(target = processJobLaunch, args = (node, job, job.file)).start()
        return job.jobId
    else:
        return None