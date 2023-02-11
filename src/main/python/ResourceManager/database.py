from id_generator import IDGenerator
from copy import deepcopy


class Database():
    def __init__(self):
        # key -> ID, value -> data about each artifact
        self.pods = dict()
        self.nodes = dict()
        self.jobs = dict()
        # initialize the ID generators
        self.pod_id_generator = IDGenerator(prefix='pod')
        self.node_id_generator = IDGenerator(prefix='node')
        self.job_id_generator = IDGenerator(prefix='job')
    
    def add_pod(self, pod: dict) -> str:
        assert pod.get('name', None) is not None
        # generate pod ID
        id = self.pod_id_generator.generate_id()
        # create required data object
        data = {
            "name": pod['name'],
            "nodes": []
        }
        # insert the data into pods table
        self.pods[id] = data
        # return pod ID
        return id

    def get_pods(self):
        return self.pods.copy()

    def get_pod(self, pod_id: str):
        return self.get_pods().get(pod_id, None)
    
    def delete_pod(self, pod_id: str):
        try:
            return self.pods.pop(pod_id)
        except KeyError:
            return None

    def add_node(self, node: dict) -> str:
        assert node.get('name', None) is not None and node.get('pod_id', None) is not None and node.get('status', None) is not None
        # ensure that the pod to which the node needs to be added exists
        if node['pod_id'] not in self.pods.keys():
            return
        # generate node ID
        id = self.node_id_generator.generate_id()
        # create the data object
        data = {
            "name": node['name'],
            "pod_id": node['pod_id'],
            "status": node['status'],
            "cpu": node.get('cpu', None),
            "memory": node.get('memory', None),
            "storage": node.get('storage', None)
        }
        # append the node ID to the associated pod record
        self.pods[node['pod_id']]['nodes'].append(id)
        # insert the data into the nodes table
        self.nodes[id] = data
        # return node ID
        return id

    def get_nodes(self):
        return self.nodes.copy()

    def get_node(self, node_id: str):
        return self.get_nodes().get(node_id, None)

    def delete_node(self, node_id: str):
        try:
            return self.nodes.pop(node_id)
        except KeyError:
            return None
    
    def add_job(self, job: dict) -> str:
        assert job.get('path', None) is not None and job.get('status', None) is not None
        # generate job ID
        id = self.job_id_generator.generate_id()
        # create the data object
        data = {
            "path": job['path'],
            "status": job['status']
        }
        # insert the data into the jobs table
        self.jobs[id] = data
        # return job ID
        return id

    def get_jobs(self):
        return self.jobs.copy()
    
    def get_job(self, job_id: str):
        return self.get_jobs().get(job_id, None)
    
    def delete_job(self, job_id: str):
        try:
            return self.jobs.pop(job_id)
        except KeyError:
            return None
