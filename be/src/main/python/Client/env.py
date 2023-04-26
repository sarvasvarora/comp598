import os
import socket


# obtain the API_HOST and API_PORT env variables
API_HOST = socket.gethostbyname(os.environ.get('API_HOST')) if os.environ.get('API_HOST') is not None else socket.gethostbyname("localhost")
API_PORT = int(os.environ.get('API_PORT')) if os.environ.get('API_PORT') is not None else 8000

# obtain the LOAD_BALANCER_HOST and LOAD_BALANCER_PORT env variables
LOAD_BALANCER_HOST = socket.gethostbyname(os.environ.get('LOAD_BALANCER_HOST')) if os.environ.get('LOAD_BALANCER_HOST') is not None else socket.gethostbyname("localhost")
LOAD_BALANCER_PORT = int(os.environ.get('LOAD_BALANCER_PORT')) if os.environ.get('LOAD_BALANCER_PORT') is not None else 7000
