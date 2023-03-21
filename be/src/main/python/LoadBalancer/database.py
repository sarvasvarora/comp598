from .status import NodeStatus, PodStatus
from .id_generator import IDGenerator
from .env import *
import os


"""
#################
# DATABASE SCHEMA
#################


pods = podId -> Pod
Pod = {
    "name" = str,
    "status" = PodStatus (HEAVY/MEDIUM/LIGHT),
    "haproxyBackendName" = str,
    "nodes" = List[str]
}


nodes = nodeId -> Node
Node = {
    "name": str,
    "podId": str,
    "uri": str,
    "status: NodeStatus (NEW (default)/ONLINE)
}
"""


class Database():
    '''
    In-memory database to store pod and node information available in the cloud infrastructure.    
    '''
    
    def __init__(self):
        self.pods = dict()
        self.nodes = dict()
        self.haproxy_server_name_generator = IDGenerator(prefix="server")


    #############
    # POD METHODS
    #############
    def _get_pod_status(self, pod_status: str) -> PodStatus:
        return {
            "heavy": PodStatus.HEAVY,
            "medium": PodStatus.MEDIUM,
            "light": PodStatus.LIGHT
        }[pod_status.lower()]
    
    def _get_pod_backend_name(self, pod_status: str) -> str:
        return {
            "heavy": HAPROXY_HEAVY_BACKEND_NAME,
            "medium": HAPROXY_MEDIUM_BACKEND_NAME,
            "light": HAPROXY_LIGHT_BACKEND_NAME
        }[pod_status.lower()]

    def add_pod(self, pod: dict) -> None:
        assert pod['podId'] is not None and pod['name'] is not None and pod['status'] is not None
        data = {
            "name": pod['name'],
            "status": self._get_pod_status(pod['status']),
            "haproxyBackendName": self._get_pod_backend_name(pod['status']),
            "nodes": []
        }
        self.pods[pod['podId']] = data

    def delete_pod(self, pod_id: str) -> None:
        node_ids = self.pods['nodes'].copy()
        for node_id in node_ids:
            self.delete_node(node_id)
        self.pods.pop(pod_id)
        # TODO: remove backend section from HAProxy config (if possible)


    ##############
    # NODE METHODS
    ##############
    def _create_haproxy_command(self, command: str) -> str:
        return f"echo '{command}' | sudo socat stdio unix-connect:{HAPROXY_SOCKET_ADDRESS}"

    def _add_haproxy_node(self, node_id: str) -> None:
        node = self.nodes[node_id]
        haproxy_backend_name = self.pods[node['podId']]['haproxyBackendName']
        haproxy_server_name = node['haproxyServerName']
        node_uri = node['uri']
        command = self._create_haproxy_command(f"experimental-mode on; add server {haproxy_backend_name}/{haproxy_server_name} {node_uri}")
        os.system(command)
    
    def _disable_haproxy_node(self, node_id: str) -> None:
        node = self.nodes[node_id]
        haproxy_backend_name = self.pods[node['podId']]['haproxyBackendName']
        haproxy_server_name = node['haproxyServerName']
        command = self._create_haproxy_command(f"experimental-mode on; disable server {haproxy_backend_name}/{haproxy_server_name}")
        os.system(command)

    def _enable_haproxy_node(self, node_id: str) -> None:
        node = self.nodes[node_id]
        haproxy_backend_name = self.pods[node['podId']]['haproxyBackendName']
        haproxy_server_name = node['haproxyServerName']
        command = self._create_haproxy_command(f"experimental-mode on; enable server {haproxy_backend_name}/{haproxy_server_name}")
        os.system(command)
    
    def _delete_haproxy_node(self, node_id: str) -> None:
        self._disable_haproxy_node(node_id)  # only disabled nodes can be deleted
        node = self.nodes[node_id]
        haproxy_backend_name = self.pods[node['podId']]['haproxyBackendName']
        haproxy_server_name = node['haproxyServerName']
        command = self._create_haproxy_command(f"experimental-mode on; del server {haproxy_backend_name}/{haproxy_server_name}")
        os.system(command)

    def add_node(self, node: dict) -> None:
        assert node['nodeId'] is not None and node['name'] is not None and node['podId'] is not None and node['uri'] is not None
        data = {
            "name": node['name'],
            "podId": node['podId'],
            "uri": node['uri'],
            "haproxyServerName": self.haproxy_server_name_generator.generate_id(),
            "status": NodeStatus.NEW
        }
        self.nodes[node['nodeId']] = data
        self.pods[node['podId']]['nodes'].append(node['nodeId'])
        self._add_haproxy_node(node['nodeId'])
        self._disable_haproxy_node(node['nodeId'])  # the server will not be enabled until it's status changes to ONLINE i.e., a job is launched on the server
    
    def update_node_status(self, node_id: str, node_status: NodeStatus | str) -> None:
        self.nodes[node_id]['status'] = node_status
        if node_status == NodeStatus.ONLINE or node_status.lower() == "online":
            self._enable_haproxy_node(node_id)
        else:
            self._delete_haproxy_node(node_id)
    
    def delete_node(self, node_id: str) -> None:
        node = self.nodes.pop(node_id)
        self.pods[node['podId']]['nodes'].remove(node_id)
        self._delete_haproxy_node(node_id)