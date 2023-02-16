import os
import socket


PROXY_HOST = socket.gethostbyname(os.environ.get('PROXY_HOST')) if os.environ.get('PROXY_HOST') is not None else socket.gethostbyname("localhost")
PROXY_PORT = int(os.environ.get('PROXY_PORT')) if os.environ.get('PROXY_PORT') is not None else 8000
ROOT_DIR = os.getcwd()
NUM_NODES = int(os.environ.get('NUM_NODES')) if os.environ.get('NUM_NODES') is not None else 10