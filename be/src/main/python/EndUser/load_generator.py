import certifi
from io import BytesIO 
import sys, os
import socket
import time
import threading
from statistics import mean
import requests
import json

class RepeatedTimer(object):
  def __init__(self, interval, limit, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.limit = limit + 3
    self.counter = 0
    self.latencies = []
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    t = self.function(*self.args, **self.kwargs)
    self.latencies.append(t)

  def start(self):
    self.counter += 1
    if self.counter > self.limit:
        print(self.latencies)
        print(f'Average latency is {mean(self.latencies)}')
        exit()
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False

LOAD_BALANCER_HOST = "10.140.17.115"
LOAD_BALANCER_PORT = 7000

def main():
    # Every freq there will be a new req
    freq = sys.argv[1] 
    numReq = sys.argv[2]
    # Type of the job to invoke
    jobType = sys.argv[3]

    r  = RepeatedTimer(float(freq), int(numReq) , makeReq, jobType)
    r.start()

def makeReq(jobType):
    start = time.time()
    res = requests.get(f'http://10.140.17.115:7000/api/{jobType}')
    print(res.json())
    duration = time.time() - start

    return duration


# Call example: python3 load_generator.py [rps] [numReq] [jobType]
# For instance python3 load_generator.py 2 10 light -> Sends 10 requests to the loadbalancer/light every 2 seconds
if __name__ == '__main__':
    main()