from fastapi import FastAPI, UploadFile, Body, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
import socket
import json
from json import JSONDecodeError
from .database import Database
from .models import *
from .status import *
from .env import *
from .job_runner import *

# create new sockets for each type of proxy
HEAVY_SOCKET = socket.socket()
MEDIUM_SOCKET = socket.socket()
LIGHT_SOCKET = socket.socket()



SOCKETS = [HEAVY_SOCKET, MEDIUM_SOCKET, LIGHT_SOCKET]
SOCKET_HOST = {HEAVY_SOCKET: HEAVY_HOST, MEDIUM_SOCKET: MEDIUM_HOST, LIGHT_SOCKET: LIGHT_HOST}
SOCKET_PORT = {HEAVY_SOCKET: HEAVY_PORT, MEDIUM_SOCKET: MEDIUM_PORT, LIGHT_SOCKET: LIGHT_PORT}

# initialize the in-memory database
database = Database()

# initialize the FastAPI app
app = FastAPI()

# enable CORS
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize the default pod ID and cluster ID
DEFAULT_CLUSTER_ID = None
DEFAULT_POD_ID = None

# cloud init check
CLOUD_INIT = False


################
# ROOT ENDPOINT
################
@app.get("/")
async def read_root():
    return {"Hello, World!"}


#######################
# CLOUD INIT ENDPOINT
#######################
@app.get("/init")
async def init():
    global DEFAULT_CLUSTER_ID, CLOUD_INIT
    if CLOUD_INIT:
        return {
            "res": "fail",
            "msg": "Cloud is already initialized for use."
        }
    # create the default cluster with a pod
    default_cluster = {
        "name": DEFAULT_CLUSTER_NAME,
        "pods": []
    }
    DEFAULT_CLUSTER_ID = database.add_cluster(default_cluster)
    heavy_pod = {
    "name": "HEAVY_POD",
    "clusterId": DEFAULT_CLUSTER_ID,
    "nodes": []
    }
    medium_pod = {
        "name": "MEDIUM_POD",
        "clusterId": DEFAULT_CLUSTER_ID,
        "nodes": []
    }
    light_pod = {
        "name": "LIGHT_POD",
        "clusterId": DEFAULT_CLUSTER_ID,
        "nodes": []
    }
    SOCKET_POD = {HEAVY_SOCKET: heavy_pod, MEDIUM_SOCKET: medium_pod, LIGHT_SOCKET: light_pod}


    for SOCKET in SOCKETS:
    # The init command on the proxy side will create default nodes under the default pod
        try:
            database.add_pod(SOCKET_POD[SOCKET])
            SOCKET.connect((SOCKET_HOST[SOCKET], SOCKET_PORT[SOCKET]))
            msg = json.dumps({
                "cmd": "init",
                "defaultPodName": SOCKET_POD[SOCKET]["name"]
            }).encode('utf-8')
            SOCKET.send(msg)
            resp = SOCKET.recv(8192).decode('utf-8')
            print(json.loads(resp))
        except:
            database.delete_cluster(DEFAULT_CLUSTER_ID)
            database.delete_pod(SOCKET_POD[SOCKET])
            return {
                "res": "fail",
                "msg": "Failed to connect to the proxy server"
            }
    CLOUD_INIT = True
    return {
        "res": "successful",
        "msg": "Cloud initialization successfully completed."
    }


###################
# CLUSTER ENDPOINTS
###################
@app.post("/clusters")
async def create_cluster(cluster: ClusterReq):
    cluster = jsonable_encoder(cluster)
    cluster_id = database.add_cluster(cluster)
    return {"clusterId": cluster_id}

@app.get("/clusters")
async def read_clusters():
    clusters = database.get_clusters()
    return {"Clusters": [{cluster_id: clusters[cluster_id]} for cluster_id in clusters.keys()]}

@app.get("/clusters/{cluster_id}")
async def read_cluster(cluster_id: str):
    cluster = database.get_cluster(cluster_id)
    return {"cluster": cluster} if cluster else {f"The specified cluster with clusterId: {cluster_id} doesn't exist."}

@app.get("/clusters/{cluster_id}/pods")
async def read_cluster_nodes(cluster_id: str):
    cluster = database.get_cluster(cluster_id)
    if not cluster:
        return {f"The specified cluster with clusterId: {cluster_id} doesn't exist."}
    pods = database.get_pods()
    return {"Pods": [{pod_id: pods[pod_id]} for pod_id in cluster['pods']]}

@app.delete("/clusters/{cluster_id}")
async def delete_cluster(cluster_id: str):
    if cluster_id == DEFAULT_CLUSTER_ID:
        return {"Cannot delete the default cluster."}
    cluster = database.delete_cluster(cluster_id)
    return {"cluster": cluster} if cluster is not None else {"Cannot delete the specified cluster because it has pods registered with it."}


################
# POD ENDPOINTS
################
@app.post("/pods")
async def create_pod(pod: PodReq):
    pod = jsonable_encoder(pod)
    if pod.get('clusterId', None) is None:
        pod['clusterId'] = DEFAULT_CLUSTER_ID
    pod_id = database.add_pod(pod)
    return {"podId": pod_id} if pod_id else {"Unable to add pod. Please specify a valid cluster ID."}

@app.get("/pods")
async def read_pods():
    pods = database.get_pods()
    return {"Pods": [{pod_id: pods[pod_id]} for pod_id in pods.keys()]}

@app.get("/pods/{pod_id}")
async def read_pod(pod_id: str):
    pod = database.get_pod(pod_id)
    return {"pod": pod} if pod else {f"The specified pod with podId: {pod_id} doens't exist."}

@app.get("/pods/{pod_id}/nodes")
async def read_pod_nodes(pod_id: str):
    pod = database.get_pod(pod_id)
    if not pod:
        return {f"The specified pod with podId: {pod_id} doesn't exist."}
    nodes = database.get_nodes()
    return {"Nodes": [{node_id: nodes[node_id]} for node_id in pod['nodes']]}

@app.delete("/pods/{pod_id}")
async def delete_pod(pod_id: str):
    if pod_id == DEFAULT_POD_ID:
        return {"Cannot delete the default pod."}
    pod = database.delete_pod(pod_id)
    return {"pod": pod} if pod is not None else {"Cannot delete the specified pod because it has nodes registered with it."}


#################
# NODE ENDPOINTS
#################
@app.post("/nodes")
async def create_node(node: NodeReq):
    # add node to the database
    node = jsonable_encoder(node)
    if node.get('podId', None) is None:
        node['podId'] = DEFAULT_POD_ID
    node['status'] = NodeStatus.IDLE
    node_id = database.add_node(node)

    if node_id is not None:
        # send msg to proxy to create node in the backend
        try:
            msg = json.dumps({
                "cmd": "node register",
                "nodeName": database.get_node(node_id).get('name'),
                "podName": database.get_pod(database.get_node(node_id).get('podId')).get('name')
            }).encode('utf-8')
            PROXY_SOCKET.send(msg)
            resp = json.loads(PROXY_SOCKET.recv(8192).decode('utf-8'))
        except:
            database.delete_node(node_id)
            return {"An internal error occured while registering the specified node."}

        # node was created -> schedule a job to execute on the node and return the node ID
        if resp['status'] == 200:
            pending_job_id = get_first_registered_job(database)
            if pending_job_id:
                # assign the job to the current node
                execute_job(pending_job_id, node_id, database, PROXY_SOCKET)
                print(f"Pending job with jobId: {pending_job_id} is now assigned to node with nodeId: {node_id}")
                return {
                    "nodeId": node_id,
                    "msg": f"Pending job with jobId: {pending_job_id} was assigned to this node."
                }
            else:
                return {"nodeId": node_id}

    return {"Unable to add node. Please specify a valid pod ID."}

@app.get("/nodes")
async def read_nodes():
    nodes = database.get_nodes()
    return {"Nodes": [{node_id: nodes[node_id]} for node_id in nodes.keys()]}

@app.get("/nodes/{node_id}")
async def read_node(node_id: str):
    node = database.get_node(node_id)
    return {"node": node} if node else {f"The specified node with nodeId: {node_id} doesn't exist."}

@app.delete("/nodes/{node_id}")
async def delete_node(node_id: str):
    node = database.get_node(node_id)
    if not node:
        return {"Unable to delete node. Specified node ID doesn't exist."}
    if node['status'] == NodeStatus.IDLE or node['status'] == NodeStatus.IDLE.value:
        try:
            msg = json.dumps({
                "cmd": "node rm",
                "nodeName": node['name'],
                "podName": database.get_pod(node['podId']).get('name')
            }).encode('utf-8')
            PROXY_SOCKET.send(msg)
            resp = json.loads(PROXY_SOCKET.recv(8192).decode('utf-8'))
            print(resp)
            # delete the node from the database
            node = database.delete_node(node_id)
            return {
                "node": node,
                "msg": "Successfully deleted node."
            }
        except:
            return {"Unable to delete node. Internal server error."}

    return {"Unable to delete node. The node is not in IDLE status."}


################
# JOB ENDPOINTS
################
@app.post("/jobs")
async def create_job(job: JobReq = Body(...), job_file: UploadFile = File(...)):
    # Make docker cmd call to create node
    job = jsonable_encoder(job)
    job['status'] = JobStatus.REGISTERED
    job['content'] = job_file.file.read().decode('utf-8')
    job_id = database.add_job(job)

    # find an idle node
    node_id = get_first_available_node(database)
    if node_id:
        execute_job(job_id, node_id, database, PROXY_SOCKET)
        return {
            "jobId": job_id,
            "msg": f"Job dispatched to be executed at node with nodeId: {node_id}"
        }
    else:
        return {
            "jobId": job_id,
            "msg": "No idle node available to dispatch the job at the moment. Job will be executed as soon as a node becomes available."
        }

@app.get("/jobs")
async def read_jobs():
    jobs = database.get_jobs()
    return {"Jobs": [{job_id: jobs[job_id]} for job_id in jobs.keys()]}

@app.get("/jobs/aborted")
async def read_aborted_jobs():
    jobs = database.get_aborted_jobs()
    return {"AbortedJobs": [{job_id: jobs[job_id]} for job_id in jobs.keys()]}

@app.get("/jobs/{job_id}")
async def read_job(job_id: str):
    job = database.get_job(job_id)
    return {"job": job} if job else {f"The specified job with jobId: {job_id} doens't exist."}

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    job = database.get_job(job_id)
    if not job:
        return {"Unable to abort job. Specified job ID doesn't exist."}
    if job['status'] == JobStatus.COMPLETED or job['status'] == JobStatus.COMPLETED.value:
        return {"Unable to abort job. Job has already completed execution."}
    if job['status'] == JobStatus.REGISTERED or job['status'] == JobStatus.REGISTERED.value:
        job = database.delete_job(job_id)
        return {
            "job": job,
            "msg": "Aborted job successfully."
        }
    if job['status'] == JobStatus.RUNNING or job['status'] == JobStatus.RUNNING.value:
        #TODO: Should we send a signal to the docker container to drop the work?
        try:
            node_id = job['nodeId']
            node = database.get_node(node_id)
            node['status'] = NodeStatus.IDLE
            job['status'] = JobStatus.ABORTED
            job = database.delete_job(job_id)
            
            # now that the node is IDLE, assign a job to it
            pending_job_id = get_first_registered_job(database)
            if pending_job_id: 
                print(f"Pending job with jobId: {pending_job_id} dispatched to node with nodeId: {node_id}")
                execute_job(pending_job_id, node_id, database, PROXY_SOCKET)
                return {
                    "job": job,
                    "msg": f"Aborted job successfully. Pending job with jobId: {pending_job_id} dispatched to node with nodeId: {node_id}"
                }
            else:
                return {
                    "job": job,
                    "msg": "Aborted job successfully."
                }
        except:
            return {f"An error occured while aborting job {job_id}"}

################
# LOG ENDPOINTS
################
@app.get("/jobs/{job_id}/logs")
def get_job_log(job_id: str):
    job = database.get_job(job_id)
    if not job:
        return {f"Unable to fetch logs for the specified job. No job exists with jobId: {job_id}"}
    elif not (job['status'] == JobStatus.COMPLETED or job['status'] == JobStatus.COMPLETED.value):
        return {"No logs available for the specified job as it has not yet completed execution. Please try again after some time."}
    else:
        node_id = job['nodeId']
        node = database.get_node(node_id)
        if not node:
            return {f"Unable to fetch logs for this job as the associated node with nodeId: {node_id} does not exist anymore."}
        pod_id = node['podId']
        pod = database.get_pod(pod_id)
        # fetch the log file from the proxy
        msg = json.dumps({
            "cmd": "job log",
            "nodeName": node['name'],
            "podName": pod['name'],
            "jobId": job_id
        }).encode('utf-8')
        try:
            PROXY_SOCKET.send(msg)
            resp = json.loads(PROXY_SOCKET.recv(8192).decode('utf-8'))
            return {
                "jobId": job_id,
                "log": resp['log']
            }
        except:
            return {"Internal server error. Unable to fetch logs for the specified job."}


@app.get("/nodes/{node_id}/logs")
def get_node_logs(node_id: str):
    node = database.get_node(node_id)
    if not node:
        return {f"Unable to fetch logs for the specified node. No node exists with nodeId: {node_id}"}
    else: 
        pod_id = node['podId']
        pod = database.get_pod(pod_id)
        msg = json.dumps({
            "cmd": "node log",
            "nodeName": node['name'],
            "podName": pod['name']
        }).encode('utf-8')
        try:
            PROXY_SOCKET.send(msg)
            resp = json.loads(PROXY_SOCKET.recv(8192).decode('utf-8'))
            print(resp)
            return {
                "nodeId": node_id,
                "log": resp['log']
            }
        except:
            return {"Internal server error. Unable to fetch logs for the specified node."}