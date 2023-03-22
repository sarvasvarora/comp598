import os
import socket


PROXY_HOST = socket.gethostbyname(os.environ.get('PROXY_HOST')) if os.environ.get('PROXY_HOST') is not None else socket.gethostbyname("localhost")
PROXY_PORT = int(os.environ.get('PROXY_PORT')) if os.environ.get('PROXY_PORT') is not None else 8000

HEAVY_HOST= socket.gethostbyname(os.environ.get('HEAVY_HOST')) if os.environ.get('HEAVY_HOST') is not None else socket.gethostbyname("localhost")
HEAVY_PORT= int(os.environ.get('HEAVY_PORT')) if os.environ.get('HEAVY_PORT') is not None else 9000

MEDIUM_HOST= socket.gethostbyname(os.environ.get('MEDIUM_HOST')) if os.environ.get('MEDIUM_HOST') is not None else socket.gethostbyname("localhost")
MEDIUM_PORT= int(os.environ.get('MEDIUM_PORT')) if os.environ.get('MEDIUM_PORT') is not None else 9001

LIGHT_HOST= socket.gethostbyname(os.environ.get('LIGHT_HOST')) if os.environ.get('LIGHT_HOST') is not None else socket.gethostbyname("localhost")
LIGHT_PORT= int(os.environ.get('LIGHT_PORT')) if os.environ.get('LIGHT_PORT') is not None else 9002

ROOT_DIR = os.getcwd()
NUM_NODES = int(os.environ.get('NUM_NODES')) if os.environ.get('NUM_NODES') is not None else 3

LOAD_BALANCER_HOST = socket.gethostbyname(os.environ.get('LOAD_BALANCER_HOST')) if os.environ.get('LOAD_BALANCER_HOST') is not None else socket.gethostbyname("localhost")
LOAD_BALANCER_PORT = int(os.environ.get('LOAD_BALANCER_PORT')) if os.environ.get('LOAD_BALANCER_PORT') is not None else 7000