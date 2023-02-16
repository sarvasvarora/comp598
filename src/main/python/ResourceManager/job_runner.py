from threading import Thread
from .status import *
from .database import Database
import json
import socket


def execute_job(job_id: str, node_id: str, database: Database, proxy_socket: socket.socket):
    # start a new thread with the job on the specified node
    Thread(target=process_job_launch, args=(node_id, job_id, database, proxy_socket)).start()


def get_first_available_node(database: Database) -> str:
    """
    Returns the node ID of an idle node.
    """
    idle_nodes = database.get_idle_nodes()
    if not idle_nodes:
        return None
    else: 
        first_idle_node = list(idle_nodes.items())[0]
        return first_idle_node[0]


def get_first_registered_job(database: Database) -> str:
    """
    Returns the node ID of an idle node.
    """
    pending_jobs = database.get_registered_jobs()
    if not pending_jobs:
        return None
    else: 
        first_pending_job = list(pending_jobs.items())[0]
        return first_pending_job[0]


def process_job_launch(node_id: str, job_id: str, database: Database, proxy_socket: socket.socket):
    node = database.get_node(node_id)
    job = database.get_job(job_id)

    # change the job and node status accordingly
    job['nodeId'] = node_id
    job['status'] = JobStatus.RUNNING
    node['status'] = NodeStatus.RUNNING

    data = job['file'].read()

    msg = json.dumps({
        "cmd": "job launch",
        "nodeName": node['name'],
        "jobId": job_id,
        "file": data.decode('utf-8')
    }).encode('utf-8')
    proxy_socket.send(msg)
    resp = json.loads(proxy_socket.recv(8192).decode('utf-8'))

    if resp['status'] == 200:
        node['status'] = NodeStatus.IDLE
        job['status'] = JobStatus.COMPLETED

        # find another pending job to execute on this node
        pending_job_id = get_first_registered_job(database)
        if pending_job_id:
            print(f"Pending job with id {pending_job_id} is now assigned to node {node_id}")
            execute_job(pending_job_id, node_id, database, proxy_socket)