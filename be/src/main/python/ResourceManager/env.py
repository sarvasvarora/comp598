import os
import socket


# obtain the proxy host and port from environment variables
PROXY_HOST = socket.gethostbyname(os.environ.get('PROXY_HOST')) if os.environ.get('PROXY_HOST') is not None else socket.gethostbyname("localhost")
PROXY_PORT = int(os.environ.get('PROXY_PORT')) if os.environ.get('PROXY_PORT') is not None else 8000

HEAVY_HOST= socket.gethostbyname(os.environ.get('HEAVY_HOST')) if os.environ.get('HEAVY_HOST') is not None else socket.gethostbyname("localhost")
HEAVY_PORT= int(os.environ.get('HEAVY_PORT')) if os.environ.get('HEAVY_PORT') is not None else 9000

MEDIUM_HOST= socket.gethostbyname(os.environ.get('MEDIUM_HOST')) if os.environ.get('MEDIUM_HOST') is not None else socket.gethostbyname("localhost")
MEDIUM_PORT= int(os.environ.get('MEDIUM_PORT')) if os.environ.get('MEDIUM_PORT') is not None else 9001

LIGHT_HOST= socket.gethostbyname(os.environ.get('LIGHT_HOST')) if os.environ.get('LIGHT_HOST') is not None else socket.gethostbyname("localhost")
LIGHT_PORT= int(os.environ.get('LIGHT_PORT')) if os.environ.get('LIGHT_PORT') is not None else 9002

# set the default cluster name and pod name
DEFAULT_CLUSTER_NAME = os.environ.get('DEFAULT_CLUSTER_NAME') or "DEFAULT_CLUSTER"
DEFAULT_POD_NAME = os.environ.get('DEFAULT_POD_NAME') or "DEFAULT_POD"

# obtain the LOAD_BALANCER_HOST and LOAD_BALANCER_PORT env variables
LOAD_BALANCER_HOST = socket.gethostbyname(os.environ.get('LOAD_BALANCER_HOST')) if os.environ.get('LOAD_BALANCER_HOST') is not None else socket.gethostbyname("localhost")
LOAD_BALANCER_PORT = int(os.environ.get('LOAD_BALANCER_PORT')) if os.environ.get('LOAD_BALANCER_PORT') is not None else 7000