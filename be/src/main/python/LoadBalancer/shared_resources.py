from .database import Database
from .health_checker import HealthChecker
from .request_monitor import RequestMonitor
from .env import *


# initialize global objects (to be shared bw routes)
database = Database()
health_checker = HealthChecker(database)
request_monitor = RequestMonitor(REQUEST_MONITOR_LOG_FILENAME)