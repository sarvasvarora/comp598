import os


# obtain the proxy host and port from environment variables
PROXY_HOST = os.environ.get('PROXY_HOST') or "10.140.17.114"
PROXY_PORT = int(os.environ.get('PROXY_PORT')) if os.environ.get('PROXY_PORT') is not None else "8000"

# set the default cluster name and pod name
DEFAULT_CLUSTER_NAME = os.environ.get('DEFAULT_CLUSTER_NAME') or "DEFAULT_CLUSTER"
DEFAULT_POD_NAME = os.environ.get('DEFAULT_POD_NAME') or "DEFAULT_POD"