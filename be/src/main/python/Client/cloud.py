from typer import Typer, Argument, Option
from rich import print, print_json
import requests
import json
from json import JSONDecodeError
import os
import socket
from .cluster import app as cluster_app
from .pod import app as pod_app
from .node import app as node_app
from .job import app as job_app
from .env import *


# initialize the CLI app
app = Typer()

# add subcommands to the main cloud app
app.add_typer(cluster_app, name='cluster', help='Command group to interact with clusters.')
app.add_typer(pod_app, name='pod', help='Command group to interact with pods.')
app.add_typer(node_app, name='node', help='Command group to interact with nodes.')
app.add_typer(job_app, name='job', help='Command group to interact with jobs.')


@app.command()
def init():
    res = requests.get(f"http://{API_HOST}:{API_PORT}/init")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)

# run the CLI app
if __name__ == "__main__":
    app()
