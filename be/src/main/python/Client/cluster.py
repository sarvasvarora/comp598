from typer import Typer, Argument, Option
from rich import print, print_json
import requests
import json
from json import JSONDecodeError
from .env import *


app = Typer()


@app.command()
def register(cluster_name: str = Argument(..., help='Cluster name to register with the cloud.')):
    """
    Registers a new cluster with the specified name. 
    [IMPORTANT] Cluster names must be unique.
    """
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    data = json.dumps({
        "name": cluster_name
    })
    res = requests.post(f"http://{API_HOST}:{API_PORT}/clusters/", data=data, headers=headers)
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def rm(cluster_id: str = Argument(..., help='Cluster ID to remove.')):
    """
    Removes the specified cluster.
    [IMPORTANT] The command fails if there are pods registered to this cluster or if the specified cluster is the default cluster.
    """
    res = requests.delete(f"http://{API_HOST}:{API_PORT}/clusters/{cluster_id}")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def ls():
    """
    Lists all the clusters in the cloud.
    """
    res = requests.get(f"http://{API_HOST}:{API_PORT}/clusters")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


if __name__ == "__main__":
    app()