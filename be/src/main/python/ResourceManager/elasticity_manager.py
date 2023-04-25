from threading import Timer
from .status import *
from .database import Database
import json
import socket


def monitor_pod_elasticity(pod_id: str, database: Database, proxy_socket: socket.socket):
    print("Hello")
    '''pod = database.get_pod(pod_id)

    # change the job and node status accordingly
    pod['']
    job['nodeId'] = node_id
    job['status'] = JobStatus.RUNNING
    node['status'] = NodeStatus.RUNNING

    msg = json.dumps({
        "cmd": "job launch",
        "nodeName": node['name'],
        "jobId": job_id,
        "content": job['content']
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
            execute_job(pending_job_id, node_id, database, proxy_socket)'''

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
        