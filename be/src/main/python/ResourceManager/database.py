from copy import deepcopy
from typing import IO
from collections import deque
from .id_generator import IDGenerator
from .status import *

"""
###############
DATABASE SCHEMA
###############

clusters = clusterId -> Cluster
Cluster = {
    "name": str,
    "pods": List[str]
}

pods = podId -> Pod
Pod = {
    "name": str,
    "clusterId": str
    "nodes": List[str],
    "status": PodStatus/str,
    "nodeLimit": int,
    "lowerSize": int,
    "upperSize": int,
    "cpuLowerLimit": float,
    "cpuUpperLimit": float,
    "memoryLowerLimit": float,
    "memoryUpperLimit": float,
    "elasticityEnabled": bool
}


nodes: nodeId -> Node
Node = {
    "name": str,
    "podId": str,
    "status": NodeStatus/str,
    "cpu": Optional[int],
    "memory": Optional[int],
    "storage": Optional[int]
}


jobs: jobId -> Job
Job = {
    "filename": str,
    "content": str,
    "status": JobStatus/str,
    "nodeId": str
}
AbortedJobs: deque(maxlength = 10)
"""



class Database():
    def __init__(self, max_aborted_buffer: int = 10):
        # key -> ID, value -> data about each artifact
        self.clusters = dict()
        self.pods = dict()
        self.nodes = dict()
        self.jobs = dict()
        self.aborted_jobs = deque(max_aborted_buffer * [None], max_aborted_buffer)
        # initialize the ID generators
        self.cluster_id_generator = IDGenerator(prefix='cluster')
        self.pod_id_generator = IDGenerator(prefix='pod')
        self.node_id_generator = IDGenerator(prefix='node')
        self.job_id_generator = IDGenerator(prefix='job')
    
    #################
    # CLUSTER METHODS
    #################
    def add_cluster(self, cluster: dict) -> str:
        assert cluster.get('name', None) is not None
        # generate cluster ID
        id = self.cluster_id_generator.generate_id()
        #create the required data object
        data = {
            "name": cluster['name'],
            "pods": []
        }
        # insert the data into the clusters table
        self.clusters[id] = data
        # return cluster ID
        return id
    
    def get_clusters(self):
        return self.clusters.copy()

    def get_cluster(self, cluster_id: str):
        return self.clusters.get(cluster_id, None)
    
    def delete_cluster(self, cluster_id: str):
        try:
            if self.clusters[cluster_id].get('pods', None):
                return None
            return self.clusters.pop(cluster_id)
        except KeyError:
            return None

    #############
    # POD METHODS
    #############
    def add_pod(self, pod: dict) -> str:
        assert pod.get('name', None) is not None and pod.get('clusterId', None) is not None
        # ensure that the pod to which the node needs to be added exists
        if pod['clusterId'] not in self.clusters.keys():
            return
        # generate pod ID
        id = self.pod_id_generator.generate_id()
        # create required data object 
        # At first the cpu/mem thresholds are set to default values until the user change them manually
        data = {
            "name": pod['name'],
            "clusterId": pod['clusterId'],
            "nodes": [],
            "status": pod['status'],
            "nodeLimit": pod['nodeLimit'],
            "cpuLowerLimit": 0.0,
            "cpuUpperLimit": 99.9,
            "memoryLowerLimit": 0.0,
            "memoryUpperLimit": 99.9,
            "lowerSize": 1,
            "upperSize": pod['nodeLimit'],
            "elasticityEnabled": False
        }
        # append the pod ID to the associated cluster record
        self.clusters[pod['clusterId']]['pods'].append(id)
        # insert the data into pods table
        self.pods[id] = data
        # return pod ID
        return id

    def get_pods(self):
        return self.pods.copy()

    def get_pod(self, pod_id: str):
        return self.pods.get(pod_id, None)
    
    def delete_pod(self, pod_id: str):
        try:
            if self.pods[pod_id].get('nodes', None):
                return None
            # remove the pod from the corresponding cluster's pod list
            pod = self.pods[pod_id]
            self.clusters[pod['clusterId']].get('pods').remove(pod_id)
            return self.pods.pop(pod_id)
        except KeyError:
            return None

    def update_pod_lower_limit(self, pod_id: str, cpu_lower: float, mem_lower: float):
        pod = self.pods.get(pod_id, None)

        if pod:
            pod['cpuLowerLimit'] = cpu_lower
            pod['memoryLowerLimit'] = mem_lower
            return self.pods[pod_id]
        else:
            return None

    def update_pod_upper_limit(self, pod_id: str, cpu_upper: float, mem_upper: float):
        pod = self.pods.get(pod_id, None)

        if pod:
            pod['cpuUpperLimit'] = cpu_upper
            pod['memoryUpperLimit'] = mem_upper
            return self.pods[pod_id]
        else:
            return None

    def enable_pod_elasticity(self, pod_id, lower_size, upper_size):
        pod = self.pods.get(pod_id, None)

        if pod:
            pod['lowerSize'] = lower_size
            pod['upperSize'] = upper_size
            pod['elasticityEnabled'] = True
            return self.pods[pod_id]
        else:
            return None

    def disable_pod_elasticity(self, pod_id):
        pod = self.pods.get(pod_id, None)

        if pod:
            pod['elasticityEnabled'] = False
            return self.pods[pod_id]
        else:
            return None
            
    def get_pod_cpu_thresh(self, pod_id):
        pod = self.pods.get(pod_id, None)

        if pod:
            return pod['cpuLowerLimit'], pod['cpuUpperLimit']
        else:
            return None

    def get_pod_memory_thresh(self, pod_id):
        pod = self.pods.get(pod_id, None)

        if pod:
            return pod['memoryLowerLimit'], pod['memoryUpperLimit']
        else:
            return None

    ###############
    # NODE METHODS
    ###############
    def add_node(self, node: dict) -> str:
        assert node.get('name', None) is not None and node.get('podId', None) is not None and node.get('status', None) is not None
        # ensure that the pod to which the node needs to be added exists
        if node['podId'] not in self.pods.keys():
            return
        # generate node ID
        id = self.node_id_generator.generate_id()
        # create the data object
        data = {
            "name": node['name'],
            "podId": node['podId'],
            "status": node['status'],
            "cpu": node.get('cpu', None),
            "memory": node.get('memory', None),
            "storage": node.get('storage', None)
        }
        # append the node ID to the associated pod record
        self.pods[node['podId']]['nodes'].append(id)
        # insert the data into the nodes table
        self.nodes[id] = data
        # return node ID
        return id

    def get_nodes(self):
        return self.nodes.copy()
    
    def get_idle_nodes(self):
        def filter_func(pair):
            k, v = pair
            return v['status'] == NodeStatus.IDLE or v['status'] == NodeStatus.IDLE.value
        
        return dict(filter(filter_func, self.nodes.items()))

    def get_node(self, node_id: str):
        return self.nodes.get(node_id, None)

    def delete_node(self, node_id: str):
        try:
            # remove the node from the corresponding pod's nodes list
            node = self.nodes[node_id]
            self.pods[node['podId']].get('nodes').remove(node_id)
            return self.nodes.pop(node_id)
        except KeyError:
            return None

    def get_pod_node_names(self, pod_id:str):
        result = []
        for n in self.nodes:
            node_dict = self.nodes[n]
            if node_dict['podId'] == pod_id:
                result.append(node_dict['name'])
        return result

    #############
    # JOB METHODS
    #############
    def add_job(self, job: dict) -> str:
        assert job.get('filename', None) is not None and job.get('status', None) is not None and job.get('content', None) is not None
        # generate job ID
        id = self.job_id_generator.generate_id()
        # create the data object
        data = {
            "filename": job['filename'],
            "content": job['content'],
            "status": job['status'],
            "nodeId": job.get('nodeId', None)
        }
        # insert the data into the jobs table
        self.jobs[id] = data
        # return job ID
        return id

    def get_jobs(self):
        return self.jobs.copy()

    def get_registered_jobs(self):
        def filter_func(pair):
            k, v = pair
            return v['status'] == JobStatus.REGISTERED or v['status'] == JobStatus.REGISTERED.value
        
        return dict(filter(filter_func, self.jobs.items()))
    
    def get_job(self, job_id: str):
        return self.jobs.get(job_id, None)
    
    def get_aborted_jobs(self):
        res = dict()
        for job in self.aborted_jobs:
            if job is not None:
                res.update(job)
        return res
    
    def delete_job(self, job_id: str):
        try:
            job = self.jobs.pop(job_id)
            self.aborted_jobs.appendleft({job_id: job})
            return job
        except KeyError:
            return None
