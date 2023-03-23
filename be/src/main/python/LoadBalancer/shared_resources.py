from .database import Database
from .request_monitor import RequestMonitor
from .env import *


# initialize global objects (to be shared bw routes)
database = Database()
request_monitor = RequestMonitor(REQUEST_MONITOR_LOG_FILENAME)