from fastapi import FastAPI, UploadFile, Body, File
from fastapi.encoders import jsonable_encoder
import socket
import json
from json import JSONDecodeError
from .database import Database
from .models import *
from .status import *
from .env import *
from .job_runner import *

# create a new socket
PROXY_SOCKET = socket.socket()

# initialize the in-memory database
database = Database()

# initialize the FastAPI app
app = FastAPI()

# initialize the default pod ID and cluster ID
DEFAULT_CLUSTER_ID = None
DEFAULT_POD_ID = None


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
    global DEFAULT_CLUSTER_ID, DEFAULT_POD_ID
    # create the default cluster with a pod
    default_cluster = {
        "name": DEFAULT_CLUSTER_NAME,
        "pods": []
    }
    DEFAULT_CLUSTER_ID = database.add_cluster(default_cluster)
    default_pod = {
        "name": DEFAULT_POD_NAME,
        "clusterId": DEFAULT_CLUSTER_ID,
        "nodes": []
    }
    DEFAULT_POD_ID = database.add_pod(default_pod)

    # The init command on the proxy side will create default nodes under the default pod
    try:
        PROXY_SOCKET.connect((PROXY_HOST, PROXY_PORT))
        msg = json.dumps({
            "cmd": "init"
        }).encode('utf-8')
        PROXY_SOCKET.send(msg)
        resp = PROXY_SOCKET.recv(8192).decode('utf-8')
        print(json.loads(resp))
    except:
        database.delete_cluster(DEFAULT_CLUSTER_ID)
        database.delete_pod(DEFAULT_POD_ID)
        return {
            "res": "fail",
            "msg": "Failed to connect to the proxy server"
        }

    return {
        "res": "successful",
        "msg": "Cloud initialization successfully completed."
    }


###################
# CLUSTER ENDPOINTS
###################
@app.post("/clusters")
async def create_cluster(cluster: Cluster):
    cluster = jsonable_encoder(cluster)
    cluster_id = database.add_cluster(cluster)
    return {"clusterId": cluster_id}

@app.get("/clusters")
async def read_clusters():
    return {"Clusters": database.get_clusters()}

@app.get("/clusters/{cluster_id}")
async def read_cluster(cluster_id: str):
    return {"cluster": database.get_cluster(cluster_id)}

@app.get("/clusters/{cluster_id}/pods")
async def read_cluster_nodes(cluster_id: str):
    cluster = database.get_cluster(cluster_id)
    pods = database.get_pods()
    return {"Pods": [pods[pod_id] for pod_id in cluster['pods']]}

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
async def create_pod(pod: Pod):
    pod = jsonable_encoder(pod)
    if pod.get('clusterId', None) is None:
        pod['clusterId'] = DEFAULT_CLUSTER_ID
    pod_id = database.add_pod(pod)
    return {"podId": pod_id} if pod_id else {"Unable to add pod. Please specify a valid cluster ID."}

@app.get("/pods")
async def read_pods():
    return {"Pods": database.get_pods()}

@app.get("/pods/{pod_id}")
async def read_pod(pod_id: str):
    return {"pod": database.get_pod(pod_id)}

@app.get("/pods/{pod_id}/nodes")
async def read_pod_nodes(pod_id: str):
    pod = database.get_pod(pod_id)
    nodes = database.get_nodes()
    return {"Nodes": [nodes[node_id] for node_id in pod['nodes']]}

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
async def create_node(node: Node):
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
                "node_name": database.get_node(node_id).get('name'),
                "pod_name": database.get_pod(database.get_node(node_id).get('podId')).get('name')
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
    return {"Nodes": database.get_nodes()}

@app.get("/nodes/{node_id}")
async def read_node(node_id: str):
    return {"node": database.get_node(node_id)}

@app.delete("/nodes/{node_id}")
async def delete_node(node_id: str):
    node = database.get_node(node_id)
    if not node:
        return {"Unable to delete node. Specified node ID doesn't exist."}
    if node['status'] == NodeStatus.IDLE or node['status'] == NodeStatus.IDLE.value:
        try:
            msg = json.dumps({
                "cmd": "node rm",
                "node_name": node['name'],
                "pod_name": database.get_pod(node['podId']).get('name')
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
async def create_job(job: Job = Body(...), job_file: UploadFile = File(...)):
    # Make docker cmd call to create node
    job = jsonable_encoder(job)
    job['status'] = JobStatus.REGISTERED
    job['file'] = job_file.file
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
    return {"Jobs": database.get_jobs()}

@app.get("/jobs/aborted")
async def read_aborted_jobs():
    return {"AbortedJobs": database.get_aborted_jobs()}

@app.get("/jobs/{job_id}")
async def read_job(job_id: str):
    return {"job": database.get_job(job_id)}

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
    elif job['status'] != JobStatus.COMPLETED or job['status'] != JobStatus.COMPLETED.value:
        return {"No logs available for the specified job as it has not yet completed execution. Please try again after some time."}
    else:
        node_id = job['nodeId']
        node = database.get_node(node_id)
        pod_id = node['podId']
        pod = database.get_pod(pod_id)
        # fetch the log file from the proxy
        msg = json.dumps({
            "cmd": "job log",
            "node_name": node['name'],
            "pod_name": pod['name'],
            'job_id': job_id
        }).encode('utf-8')
        try:
            socket.send(msg)
            resp = json.loads(socket.recv(8192).decode('utf-8'))
            print(resp)
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
            "node_name": node['name'],
            "pod_name": pod['name']
        }).encode('utf-8')
        try:
            socket.send(msg)
            resp = json.loads(socket.recv(8192).decode('utf-8'))
            print(resp)
            return {
                "nodeId": node_id,
                "log": resp['log']
            }
        except:
            return {"Internal server error. Unable to fetch logs for the specified node."}