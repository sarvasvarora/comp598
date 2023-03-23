import pycurl
import certifi
from io import BytesIO 
import sys, os
import socket
import time
import threading
from statistics import mean

class RepeatedTimer(object):
  def __init__(self, interval, limit, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.limit = limit + interval
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

LOAD_BALANCER_HOST = socket.gethostbyname(os.environ.get('LOAD_BALANCER_HOST')) if os.environ.get('LOAD_BALANCER_HOST') is not None else socket.gethostbyname("localhost")
LOAD_BALANCER_PORT = int(os.environ.get('LOAD_BALANCER_PORT')) if os.environ.get('LOAD_BALANCER_PORT') is not None else 7000

def main():
    # Every freq there will be a new req
    freq = sys.argv[1] 
    duration = sys.argv[2]
    # Type of the job to invoke
    jobType = sys.argv[3]

    r  = RepeatedTimer(int(freq), int(duration)//int(freq) , makeReq, jobType)
    r.start()

def makeReq(jobType):
    c = pycurl.Curl()

    ## Define Options - Set URL we want to request
    c.setopt(c.URL, f'{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/api/{type}')
    #c.setopt(c.URL, f'{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}')

    ## Setup buffer to recieve response
    buffer = BytesIO()
    c.setopt(c.WRITEDATA, buffer)

    ## Setup SSL certificates
    c.setopt(c.CAINFO, certifi.where())

    ## Make Requests
    start = time.time()
    c.perform()
    duration = time.time() - start

    ## Close Connection
    c.close()

    ## Retrieve the content BytesIO & Decode
    body = buffer.getvalue()
    print(body.decode('iso-8859-1'))
    return duration


# Call example: python3 load_generator.py [rps] [duration] [jobType]
# For instance python3 load_generator.py 2 10 light -> Sends 5 requests to the loadbalancer/light every 2 seconds
if __name__ == '__main__':
    main()
