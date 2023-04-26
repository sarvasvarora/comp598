from threading import Timer
from .status import *
from .database import Database
from .env import *
import json
import socket
from random import randint

def monitor_pod_elasticity(pod_id: str, database: Database, proxy_socket: socket.socket):
    sum_cpu = 0.0
    sum_mem = 0.0

    try:
        pod = database.get_pod(pod_id)
        pod_nodes = database.get_pod_node_names(pod_id)
        num_nodes = len(pod_nodes)
        msg = json.dumps({
            "cmd": "node stats",
            "nodes": pod_nodes
        }).encode('utf-8')

        proxy_socket.send(msg)
        resp = json.loads(proxy_socket.recv(8192).decode('utf-8'))
        print(resp)
        
        ######################################################################
        # [Condition 1] Check the cpu thresholds with the average measured cpu
        ######################################################################

        cpu_avg = resp['cpu_percentage']
        cpu_lower, cpu_upper = database.get_pod_cpu_thresh(pod_id)

        # Should delete a node from the pod
        if cpu_avg < cpu_lower:
            print("Average CPU is less than the cpu_lower_thresh. Removing a node detected!")

            # Check if a node can be added
            if pod['lowerSize'] == len(pod['nodes']):
                print(f"Cannot remove a node under the {pod_id} as there is only min number of nodes in it")
            else:
                delete_node(pod_id, proxy_socket, database)

        # Should add a node to the pod
        if cpu_avg > cpu_upper:
            print("Average CPU is greater than the cpu_upper_thresh. Adding a node detected!")

            # Check if a node can be added
            if pod['upperSize'] == len(pod['nodes']):
                print(f"Cannot add a new node under the {pod_id} as there are already max number of nodes in it")
            else:
                add_node(pod_id, proxy_socket, database)


        ##########################################################################
        # [Condition 2] Check the memory thresholds with the average measured mem
        ##########################################################################

        mem_avg = resp['mem_percentage']
        mem_lower, mem_upper = database.get_pod_memory_thresh(pod_id)

        # Should delete a node from the pod
        if mem_avg < mem_lower:
            print("Average Memory Usage is less than the mem_lower_thresh. Removing a node detected!")

            # Check if a node can be added
            if pod['lowerSize'] == len(pod['nodes']):
                print(f"Cannot remove a node under the {pod_id} as there is only min number of nodes in it")
            else:
                delete_node(pod_id, proxy_socket, database)

        # Should add a node to the pod
        if mem_avg > mem_upper:
            print("Average Memory Usage is greater than the mem_upper_thresh. Adding a node detected!")

            # Check if a node can be added
            if pod['upperSize'] == len(pod['nodes']):
                print(f"Cannot add a new node under the {pod_id} as there are already max number of nodes in it")
            else:
                add_node(pod_id, proxy_socket, database)

    except Exception as e:
        print(f"An error occured: {str(e)}")

def add_node(pod_id: str, proxy_socket: socket.socket, database: Database):
    # add node to the database
    pod = database.get_pod(pod_id)
    node = {}

    # Name appended with a random 8digit number
    name = f"elastic_extra_{randint(10**7, (10**8)-1)}"
    node['name'] = name
    node['podId'] = pod_id

    # TODO: Should it be NEW or ONLINE?
    node['status'] = NodeStatus.NEW

    # Set the cpu and memory config of the node
    Pod_Host = None
    if pod['name'] == 'HEAVY_POD':
        node['cpu'] = 0.8
        node['memory'] = 500
        Pod_Host = HEAVY_HOST
    elif pod['name'] == 'MEDIUM_POD':
        node['cpu'] = 0.5
        node['memory'] = 300
        Pod_Host = MEDIUM_HOST
    elif pod['name'] == 'LIGHT_POD':
        node['cpu'] = 0.3
        node['memory'] = 100
        Pod_Host = LIGHT_HOST

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
            # TODO: Uncomment this part
            '''print(f"Sending this uri to the load balancer {Pod_Host}:{resp['port']}")
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
                return {"An error occured in the load balancer."}'''

            return resp
        except Exception as e:
            database.delete_node(node_id)
            return {f"An Error Occured: {str(e)}"}

    return {"Unable to add node. Please specify a valid pod ID."}

def delete_node(pod_id: str, proxy_socket: socket.socket, database: Database):
    pass

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
        