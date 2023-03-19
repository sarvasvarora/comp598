import os
import socket
from .database import Database
from .request_monitor import RequestMonitor
from .health_checker import HealthChecker


# obtain the API_HOST and API_PORT env variables
API_HOST = socket.gethostbyname(os.environ.get('API_HOST')) if os.environ.get('API_HOST') is not None else socket.gethostbyname("localhost")
API_PORT = int(os.environ.get('API_PORT')) if os.environ.get('API_PORT') is not None else 3000

# initialize global objects (to be shared bw routes)
database = Database()
health_checker = HealthChecker(database)
request_monitor = RequestMonitor()
