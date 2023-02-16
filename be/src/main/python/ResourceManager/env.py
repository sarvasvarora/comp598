import os
import socket


# obtain the proxy host and port from environment variables
PROXY_HOST = socket.gethostbyname(os.environ.get('PROXY_HOST')) if os.environ.get('PROXY_HOST') is not None else socket.gethostbyname("localhost")
PROXY_PORT = int(os.environ.get('PROXY_PORT')) if os.environ.get('PROXY_PORT') is not None else 8000

# set the default cluster name and pod name
DEFAULT_CLUSTER_NAME = os.environ.get('DEFAULT_CLUSTER_NAME') or "DEFAULT_CLUSTER"
DEFAULT_POD_NAME = os.environ.get('DEFAULT_POD_NAME') or "DEFAULT_POD"