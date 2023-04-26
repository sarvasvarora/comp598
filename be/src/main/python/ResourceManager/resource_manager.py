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
from .elasticity_manager import *
import requests
from random import randint

# create new sockets for each type of proxy
HEAVY_SOCKET = socket.socket()
MEDIUM_SOCKET = socket.socket()
LIGHT_SOCKET = socket.socket()

SOCKETS = [HEAVY_SOCKET, MEDIUM_SOCKET, LIGHT_SOCKET]
SOCKET_HOST = {HEAVY_SOCKET: HEAVY_HOST, MEDIUM_SOCKET: MEDIUM_HOST, LIGHT_SOCKET: LIGHT_HOST}
SOCKET_PORT = {HEAVY_SOCKET: HEAVY_PORT, MEDIUM_SOCKET: MEDIUM_PORT, LIGHT_SOCKET: LIGHT_PORT}
ID_TO_SOCKET = {"pod_0": HEAVY_SOCKET, "pod_1": MEDIUM_SOCKET, "pod_2": LIGHT_SOCKET}

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

# Store for pods' Elasticity Timers in case we want to start/stop them multiple times
# Key -> pod_id     value -> RT Object
ELASTICITY_TIMERS = {}

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
    "nodes": [],
    "status": PodStatus.RUNNING,
    "nodeLimit": 10
    }
    medium_pod = {
        "name": "MEDIUM_POD",
        "clusterId": DEFAULT_CLUSTER_ID,
        "nodes": [],
        "status": PodStatus.RUNNING,
        "nodeLimit": 15
    }
    light_pod = {
        "name": "LIGHT_POD",
        "clusterId": DEFAULT_CLUSTER_ID,
        "nodes": [],
        "status": PodStatus.RUNNING,
        "nodeLimit": 20
    }
    SOCKET_POD = {HEAVY_SOCKET: heavy_pod, MEDIUM_SOCKET: medium_pod, LIGHT_SOCKET: light_pod}

    for SOCKET in SOCKETS:
    # The init command on the proxy side will create default nodes under the default pod
        try:
            pod_id = database.add_pod(SOCKET_POD[SOCKET])
            SOCKET.connect((SOCKET_HOST[SOCKET], SOCKET_PORT[SOCKET]))
            msg = json.dumps({
                "cmd": "init",
                "defaultPodName": SOCKET_POD[SOCKET]["name"]
            }).encode('utf-8')
            SOCKET.send(msg)
            resp = SOCKET.recv(8192).decode('utf-8')
            print(json.loads(resp))

            # Call the Load balancer
            headers = {
                "Content-Type": "application/json",
                "accept": "application/json"
            }
            if SOCKET ==  HEAVY_SOCKET:
                try:
                    data = json.dumps({
                        "name": heavy_pod['name'],
                        "podId": pod_id,
                        "type": "heavy"
                    })
                    res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/pods", data=data, headers=headers)

                    # make pod active 
                    data = json.dumps({
                        "status": "active",
                    })
                    res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/pods/{pod_id}", data=data, headers=headers)
                except Exception as e:
                    print(str(e))
            elif SOCKET ==  MEDIUM_SOCKET:
                try:
                    data = json.dumps({
                        "name": medium_pod['name'],
                        "podId": pod_id,
                        "type": "medium"
                    })
                    res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/pods", data=data, headers=headers)

                    # make pod active 
                    data = json.dumps({
                        "status": "active",
                    })
                    res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/pods/{pod_id}", data=data, headers=headers)
                except Exception as e:
                    print(str(e))
            elif SOCKET == LIGHT_SOCKET:
                try:
                    data = json.dumps({
                        "name": light_pod['name'],
                        "podId": pod_id,
                        "type": "light"
                    })
                    res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/pods", data=data, headers=headers)

                    # make pod active 
                    data = json.dumps({
                        "status": "active",
                    })
                    res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/pods/{pod_id}", data=data, headers=headers)
                except Exception as e:
                    print(str(e))

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
    pod = database.get_pod(node['podId'])

    # Check for uniqueness of the name of the node
    for n_id in pod['nodes']:
        n = database.get_node(n_id)
        if n['name'] == node['name']:
            return {f"Another node with the same name exists in pod {pod['name']}"}

    # Check the limit of the nodes registered in this pod
    if pod['nodeLimit'] == len(pod['nodes']):
         return {f"Cannot add a new node under the pod as the limit of nodes is reached."}

    node['status'] = NodeStatus.NEW

    # Set the cpu and memory config of the node
    PROXY_SOCKET = None
    Pod_Host = None
    if pod['name'] == 'HEAVY_POD':
        node['cpu'] = 0.8
        node['memory'] = 500
        PROXY_SOCKET = HEAVY_SOCKET
        Pod_Host = HEAVY_HOST
    elif pod['name'] == 'MEDIUM_POD':
        node['cpu'] = 0.5
        node['memory'] = 300
        PROXY_SOCKET = MEDIUM_SOCKET
        Pod_Host = MEDIUM_HOST
    elif pod['name'] == 'LIGHT_POD':
        node['cpu'] = 0.3
        node['memory'] = 100
        PROXY_SOCKET = LIGHT_SOCKET
        Pod_Host = LIGHT_HOST

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
            print(resp)

            # Add node to the lb [with default new status]
            print(f"Sending this uri to the load balancer {Pod_Host}:{resp['port']}")
            try:
                headers = {
                    "Content-Type": "application/json",
                    "accept": "application/json"
                }
                data = json.dumps({
                    "name": node['name'],
                    "nodeId": node_id,
                    "podId": node['podId'],
                    "uri": f"{Pod_Host}:{resp['port']}",
                })
                res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/nodes", data=data, headers=headers)
                print(res)
                return res.json()
            except Exception as e:
                print(str(e))
                return {"An error occured in the load balancer."}
        except Exception as e:
            database.delete_node(node_id)
            return {f"An internal error occured: {str(e)}."}

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
    node_pod = database.get_pod(node['podId'])
    PROXY_SOCKET = None
    if not node:
        return {"Unable to delete node. Specified node ID doesn't exist."}

    # Determine which proxy to send to
    if node_pod['name'] == 'HEAVY_POD':
        PROXY_SOCKET = HEAVY_SOCKET
    elif node_pod['name'] == 'MEDIUM_POD':
        PROXY_SOCKET = MEDIUM_SOCKET
    elif node_pod['name'] == 'LIGHT_POD':
        PROXY_SOCKET = LIGHT_SOCKET

    if node['status'] == NodeStatus.NEW or node['status'] == NodeStatus.NEW.value:
        try:
            msg = json.dumps({
                "cmd": "node rm",
                "nodeName": node['name'],
                "podName": node_pod.get('name')
            }).encode('utf-8')
            PROXY_SOCKET.send(msg)
            resp = json.loads(PROXY_SOCKET.recv(8192).decode('utf-8'))
            print(resp)

            # delete the node from the database
            node = database.delete_node(node_id)
            '''return {
                "node": node,
                "msg": "Successfully deleted node."
            }'''
        except Exception as e:
            return {f"Unable to delete node. Internal server error: {str(e)}"}

    elif node['status'] == NodeStatus.ONLINE or node['status'] == NodeStatus.ONLINE.value:
        # Should notify the Load Balancer that it should not redirect traffic through it anymore.
        try:
            # First notify the lb
            res = requests.delete(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/nodes/{node_id}")
            print(res)

            # Now process delete in RM and proxy
            msg = json.dumps({
                "cmd": "node rm",
                "nodeName": node['name'],
                "podName": node_pod.get('name')
            }).encode('utf-8')
            PROXY_SOCKET.send(msg)
            resp = json.loads(PROXY_SOCKET.recv(8192).decode('utf-8'))
            print(resp)

            # delete the node from the database
            node = database.delete_node(node_id)

        except Exception as e:
            return {f"Unable to delete node. Internal server error: {str(e)}"}

    # Finally check if the removed node was the last node in the pod
    if len(node_pod.get('nodes')) == 0:
        # pause the pod
        pass

    return {'status': 200, 'message': "Successfully deleted the node"}

@app.get("/nodes/stats/{node_id}")
async def read_node_stats(node_id: str):
    # Should do it for all nodes in each pod 
    if node_id is not None:
        # send msg to proxy to create node in the backend
        try:
            print("here")
            msg = json.dumps({
                "cmd": "node stats",
                "nodeName": database.get_node(node_id).get('name'),
                "podName": database.get_pod(database.get_node(node_id).get('podId')).get('name')
            }).encode('utf-8')
            print("here")
            LIGHT_SOCKET.send(msg)
            print("here2")
            resp = json.loads(LIGHT_SOCKET.recv(8192).decode('utf-8'))
            print(resp)
            
        except Exception as e:
            return {f"An internal error occured while reading the node stats. {str(e)}"}

    return {"Error. Node_id is not valid for reading the stats."}

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

@app.get("/jobs/launch/{pod_id}")
async def launch_job_on_pod(pod_id: str):
    pod = database.get_pod(pod_id)
    print(pod)
    # pick up the first node with NEW status in the specified pod
    for n in pod['nodes']:
        node = database.get_node(n)
        jobType = None
        PROXY_SOCKET = None

        if node["status"] == NodeStatus.NEW:
            print("Found NEW node")
            # Switch status to ONLINE 
            node["status"] = NodeStatus.ONLINE
                
            # Start the HTTP web server on the node
            try:
                if pod['name'] == 'HEAVY_POD':
                    PROXY_SOCKET = HEAVY_SOCKET
                    jobType = "heavy"
                elif pod['name'] == 'MEDIUM_POD':
                    PROXY_SOCKET = MEDIUM_SOCKET
                    jobType = "medium"
                if pod['name'] == 'LIGHT_POD':
                    PROXY_SOCKET = LIGHT_SOCKET
                    jobType = "light"

                print("Set the parameters")

                msg = json.dumps({
                    "cmd": "job launch on pod",
                    "nodeName": node['name'],
                    "podName": pod['name'],
                    "type": jobType, 
                }).encode('utf-8')

                PROXY_SOCKET.send(msg)
                print("before sending to proxy")
                resp = json.loads(PROXY_SOCKET.recv(8192).decode('utf-8'))
                print("after sending to proxy")

            except Exception as e:
                return {f"Internal server error. {str(e)}"}

            # Notify the laod balancer
            # if pod["status"] == PodStatus.PAUSED -> Do not notify the LB  because the pod is paused
            if pod["status"] == PodStatus.RUNNING:
                headers = {
                    "Content-Type": "application/json",
                    "accept": "application/json"
                }
                try:
                    data = json.dumps({
                        "status": "online"
                    })
                    res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/nodes/{n}", data=data, headers=headers)
                    print(res)
                    return res.json()
                except Exception as e:
                    print("An error occured in the load balancer")
                    print(str(e))
            # Delete this line
            #return 
    
    return {"There are no NEW nodes under the specified pod. Job cannot be launched. Try out later."}

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


#######################
# ELASTICITY ENDPOINTS
#######################

@app.get('/elasticity/pods/{pod_id}')
async def get_elasticity_of_pod(pod_id: str):
    pod = database.get_pod(pod_id)
    if not pod:
        return {f"Error. The specified pod with podId: {pod_id} doesn't exist."}
    try:
        pod_info = get_pod_elasticity(pod_id, database, ID_TO_SOCKET[pod_id])
        return {'message': 200, 'pod_info': pod_info}
    except Exception as e:
        return {'message': 500, 'Error': str(e)}


@app.post("/elasticity/lower/{pod_id}/{value}")
async def set_lower_threshold(pod_id: str, value: str):
    # First verify the given pod_id
    pod = database.get_pod(pod_id)
    if not pod:
        return {f"Error. The specified pod with podId: {pod_id} doesn't exist."}
    
    try:
        value_dict = json.loads(value)
        updated_pod = database.update_pod_lower_limit(pod_id, value_dict['cpu'], value_dict['memory'])

        return {'message': 200, 'updated_pod': updated_pod}

    except Exception as e:
        return {'message': 500, 'Error': str(e)}

@app.post("/elasticity/upper/{pod_id}/{value}")
async def set_upper_threshold(pod_id: str, value: str):
    # First verify the given pod_id
    pod = database.get_pod(pod_id)
    if not pod:
        return {f"Error. The specified pod with podId: {pod_id} doesn't exist."}
    
    try:
        value_dict = json.loads(value)
        updated_pod = database.update_pod_upper_limit(pod_id, value_dict['cpu'], value_dict['memory'])

        return {'message': 200, 'updated_pod': updated_pod}

    except Exception as e:
        return {'message': 500, 'Error': str(e)}

@app.post("/elasticity/enable")
async def enable_elasticity(podRange: PodElasticityRange):

    rangeInfo = jsonable_encoder(podRange)

    # First verify the given pod_id
    pod_id = rangeInfo['podId']
    pod = database.get_pod(pod_id)

    if not pod:
        return {f"Error. The specified pod with podId doesn't exist."}
    
    try:
        updated_pod = database.enable_pod_elasticity(pod_id, rangeInfo['lower_size'], rangeInfo['upper_size'])

        # TODO: Add the checks with min/max num_nodes
        num_nodes = len(pod['nodes'])

        # Should register a NEW node for the pod
        if num_nodes < rangeInfo['lower_size']:
            for i in range(rangeInfo['lower_size'] - num_nodes):
                # Register a new node
                register_extra_node(pod, pod_id)

        # Now check if enough ONLINE nodes exist ---> If not, change NEW ones to ONLINE
        num_online = database.get_pod_num_online_node(pod_id)
        if num_online < rangeInfo['lower_size']:
            for i in range(rangeInfo['lower_size'] - num_online):
                # Change the NEW nodes to ONLINE
                add_extra_online_nodes(pod, pod_id)

        # TODO: Should add checks for rangeInfo['upper_size'] also

        # Elasticity Manager should be able to communicate with the proxy
        PROXY_SOCKET = None
        if updated_pod['name'] == 'HEAVY_POD':
            PROXY_SOCKET = HEAVY_SOCKET
        elif updated_pod['name'] == 'MEDIUM_POD':
            PROXY_SOCKET = MEDIUM_SOCKET
        elif updated_pod['name'] == 'LIGHT_POD':
            PROXY_SOCKET = LIGHT_SOCKET
        
        # TODO: Configure the frequency!
        elasticity_timer = RepeatedTimer(15, monitor_pod_elasticity, pod_id, database, PROXY_SOCKET)
        ELASTICITY_TIMERS[pod_id] = elasticity_timer
        ELASTICITY_TIMERS[pod_id].start()

        return {'message': 200, 'updated_pod': updated_pod}

    except Exception as e:
        return {'message': 500, 'Error': str(e)}

@app.get("/elasticity/disable/{pod_id}")
async def disable_elasticity(pod_id: str):

    # First verify the given pod_id
    pod = database.get_pod(pod_id)

    if not pod:
        return {f"Error. The specified pod with podId doesn't exist."}
    
    try:
        # Get the elasticity_timer of the specified pod and stop it
        ELASTICITY_TIMERS[pod_id].stop()

        # Update database
        updated_pod = database.disable_pod_elasticity(pod_id)

        return {'message': 200, 'updated_pod': updated_pod}

    except Exception as e:
        return {'message': 500, 'Error': str(e)}

# Register one node with NEW status under the pod
def register_extra_node(pod, pod_id):
    node = {}

    # Name appended with a random 8digit number
    name = f"elastic_extra_{randint(10**7, (10**8)-1)}"
    node['name'] = name
    node['podId'] = pod_id

    node['status'] = NodeStatus.NEW

    # Set the cpu and memory config of the node
    Pod_Host = None
    jobType = None
    proxy_socket = None
    if pod['name'] == 'HEAVY_POD':
        node['cpu'] = 0.8
        node['memory'] = 500
        Pod_Host = HEAVY_HOST
        jobType = "heavy"
        proxy_socket = HEAVY_SOCKET
    elif pod['name'] == 'MEDIUM_POD':
        node['cpu'] = 0.5
        node['memory'] = 300
        Pod_Host = MEDIUM_HOST
        jobType = "medium"
        proxy_socket = MEDIUM_SOCKET
    elif pod['name'] == 'LIGHT_POD':
        node['cpu'] = 0.3
        node['memory'] = 100
        Pod_Host = LIGHT_HOST
        jobType = "light"
        proxy_socket = LIGHT_SOCKET

    node_id = database.add_node(node)

    if node_id is not None:
        # send msg to proxy to create node in the backend
        try:
            msg = json.dumps({
                "cmd": "node register",
                "nodeName": database.get_node(node_id).get('name'),
                "podName": pod['name']
            }).encode('utf-8')
            proxy_socket.send(msg)
            resp = json.loads(proxy_socket.recv(8192).decode('utf-8'))
            print(resp)

            # Add node to the lb [with default new status]
            print(f"Sending this uri to the load balancer {Pod_Host}:{resp['port']}")
            headers = {
                "Content-Type": "application/json",
                "accept": "application/json"
            }
            data = json.dumps({
                "name": node['name'],
                "nodeId": node_id,
                "podId": node['podId'],
                "uri": f"{Pod_Host}:{resp['port']}",
            })
            res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/nodes", data=data, headers=headers)
            print(res.json())
            return

        except Exception as e:
            print(f"An error occured in adding an extra node: {str(e)}")
            return

# Converts one of the new nodes to online node
def add_extra_online_nodes(pod, pod_id):
    for n in pod['nodes']:
        node = database.get_node(n)
        if node['status'] == NodeStatus.ONLINE or node['status'] == NodeStatus.ONLINE.value:
            continue 
        else:
            # Found a NEW node      ------>     Launch a job on it + update database + let the LB know
            
            # Switch status to ONLINE 
            node["status"] = NodeStatus.ONLINE
                
            # Start the HTTP web server on the node
            try:
                if pod['name'] == 'HEAVY_POD':
                    jobType = "heavy"
                    proxy_socket = HEAVY_SOCKET
                elif pod['name'] == 'MEDIUM_POD':
                    jobType = "medium"
                    proxy_socket = MEDIUM_SOCKET
                if pod['name'] == 'LIGHT_POD':
                    jobType = "light"
                    proxy_socket = LIGHT_SOCKET

                msg = json.dumps({
                    "cmd": "job launch on pod",
                    "nodeName": node['name'],
                    "podName": pod['name'],
                    "type": jobType, 
                }).encode('utf-8')

                proxy_socket.send(msg)
                resp = json.loads(proxy_socket.recv(8192).decode('utf-8'))
                print(resp)

            except Exception as e:
                return {f"Internal server error. {str(e)}"}

            # Notify the laod balancer
            if pod["status"] == PodStatus.RUNNING:
                print("Notify the new ONLINE node to the LB")
                headers = {
                    "Content-Type": "application/json",
                    "accept": "application/json"
                }
                try:
                    data = json.dumps({
                        "status": "online"
                    })
                    res = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/nodes/{n}", data=data, headers=headers)
                    print(res.json())
                    return
                except Exception as e:
                    print(f"An error occured in the load balancer: {str(e)}")
                    return