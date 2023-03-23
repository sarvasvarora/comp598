from typing import Literal, List
from datetime import datetime, timedelta


class RequestMonitor():
    '''
    Class to keep track of incoming requests and note down the response time
    '''
    def __init__(self, log_filename: str):
        self.requests = {
            "heavy": [],
            "medium": [],
            "light": []
        }
        self.throughputs = {
            "heavy": [],
            "medium": [],
            "light": []
        }
        self.num_req = {
            "heavy": 0,
            "medium": 0,
            "light": 0
        }
        self.total_response_time = {
            "heavy": 0.0,
            "medium": 0.0,
            "light": 0.0
        }
        self.prev_time = datetime.now()
        self.log = open(log_filename, 'wt')

    def __del__(self):
        self.log.close()

    def _compute_throughput(self, job_type: str, response_time: float | int):
        self.num_req[job_type] += 1
        self.total_response_time[job_type] += response_time
        # recompute and log the throughput every 5 seconds
        if (datetime.now() - self.prev_time) > timedelta(seconds=5):
            for j in ('heavy', 'medium', 'light'):
                throughput = self.num_req[j] / self.total_response_time[j] if self.total_response_time[j] > 0 else "inf"
                self.log.write(f"job_type: {j} | throughput: {throughput} | total_requests: {self.num_req[j]} | total_response_time: {self.total_response_time[j]}\n")
                self.throughputs[j].append({
                    "throughput": throughput,
                    "totalRequests": self.num_req[j],
                    "totalResponseTime": self.total_response_time[j]
                })
                # reset the counters
                self.num_req[j] = 0
                self.total_response_time[j] = 0.0
        self.prev_time = datetime.now()

    def log_request(
            self,
            job_type: Literal['heavy', 'medium', 'light'],
            client_host: str,
            request_arrival_time: datetime,
            response_time: float | int
        ):
        self.requests[job_type].append({
            "clientHost": client_host,
            "requestArrivalTime": request_arrival_time,
            "responseTime": response_time
        })
        # log the request
        self.log.write(f"job_type: {job_type} | client_host: {client_host} | request_arrival_time: {request_arrival_time} | response_time: {response_time}\n")
        # compute throughput
        self._compute_throughput(job_type, response_time)

    def log_pod_status(self, job_type: Literal['heavy', 'medium', 'light'], pod_status: Literal['active', 'inactive']):
        self.log.write(f"job_type: {job_type} | pod_status: {pod_status}\n")

    def log_num_nodes(self, job_type: Literal['heavy', 'medium', 'light'], num_nodes: int):
        self.log.write(f"job_type: {job_type} | num_nodes: {num_nodes}\n")

    def get_heavy_requests(self):
        return self.requests['heavy']

    def get_medium_requests(self):
        return self.requests['medium']

    def get_light_requests(self):
        return self.requests['light']

    def get_throughputs(self):
        return self.throughputs