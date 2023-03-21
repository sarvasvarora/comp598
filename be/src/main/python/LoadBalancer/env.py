import os
import socket


# obtain the API_HOST and API_PORT env variables
API_HOST = socket.gethostbyname(os.environ.get('API_HOST')) if os.environ.get('API_HOST') is not None else socket.gethostbyname("localhost")
API_PORT = int(os.environ.get('API_PORT')) if os.environ.get('API_PORT') is not None else 3000

# obtain the LOAD_BALANCER_HOST and LOAD_BALANCER_PORT env variables
LOAD_BALANCER_HOST = socket.gethostbyname(os.environ.get('LOAD_BALANCER_HOST')) if os.environ.get('LOAD_BALANCER_HOST') is not None else socket.gethostbyname("localhost")
LOAD_BALANCER_PORT = int(os.environ.get('LOAD_BALANCER_PORT')) if os.environ.get('LOAD_BALANCER_PORT') is not None else 7000

# HAPROXY env variables
HAPROXY_SOCKET_ADDRESS = os.environ.get('HAPROXY_SOCKET_ADDRESS') if os.environ.get('HAPROXY_SOCKET_ADDRESS') is not None else "/run/haproxy/haproxy.sock"
HAPROXY_HEAVY_BACKEND_NAME = os.environ.get('HAPROXY_HEAVY_BACKEND_NAME') if os.environ.get('HAPROXY_HEAVY_BACKEND_NAME') is not None else "heavy_backend"
HAPROXY_MEDIUM_BACKEND_NAME = os.environ.get('HAPROXY_MEDIUM_BACKEND_NAME') if os.environ.get('HAPROXY_MEDIUM_BACKEND_NAME') is not None else "medium_backend"
HAPROXY_LIGHT_BACKEND_NAME = os.environ.get('HAPROXY_LIGHT_BACKEND_NAME') if os.environ.get('HAPROXY_LIGHT_BACKEND_NAME') is not None else "light_backend"
