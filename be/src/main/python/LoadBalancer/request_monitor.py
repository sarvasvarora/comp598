from typing import Literal
from datetime import datetime, timedelta


class RequestMonitor():
    '''
    Class to keep track of incoming requests and note down the response time
    '''
    def __init__(self, log_filename: str):
        self.heavy_jobs = []
        self.medium_jobs = []
        self.light_jobs = []
        self.throughputs = []
        self.num_req = 0
        self.total_response_time = 0.0
        self.prev_time = datetime.now()
        self.log = open(log_filename, 'wt')

    def __del__(self):
        self.log.close()

    def _compute_throughput(self, job_type: str, response_time: float | int):
        self.num_req += 1
        self.total_response_time += response_time
        # recompute and log the throughput every 5 seconds
        if (datetime.now() - self.prev_time) > timedelta(seconds=5):
            throughput = self.num_req / self.total_response_time if self.total_response_time > 0 else "inf"
            self.log.write(f"job_type: {job_type} | throughput: {throughput} | total_requests: {self.num_req} | total_response_time: {self.total_response_time}\n")
            self.throughputs.append(throughput)
            self.num_req = 0
            self.total_response_time = 0.0
        self.prev_time = datetime.now()

    def log_request(
            self,
            job_type: Literal['heavy', 'medium', 'light'],
            client_host: str,
            request_arrival_time: datetime,
            response_time: float | int
        ):
        match job_type:
            case "heavy":
                self.heavy_jobs.append((client_host, request_arrival_time, response_time))
            case "medium":
                self.medium_jobs.append((client_host, request_arrival_time, response_time))
            case "light":
                self.light_jobs.append((client_host, request_arrival_time, response_time))
        # log the request
        self.log.write(f"job_type: {job_type} | client_host: {client_host} | request_arrival_time: {request_arrival_time} | response_time: {response_time}\n")
        # compute throughput
        self._compute_throughput(job_type, response_time)

    def log_pod_status(self, job_type: Literal['heavy', 'medium', 'light'], pod_status: Literal['active', 'inactive']):
        self.log.write(f"job_type: {job_type} | pod_status: {pod_status}\n")

    def log_num_nodes(self, job_type: Literal['heavy', 'medium', 'light'], num_nodes: int):
        self.log.write(f"job_type: {job_type} | num_nodes: {num_nodes}\n")
