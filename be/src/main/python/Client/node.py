from typer import Typer, Argument, Option
from rich import print, print_json
import requests
import json
from json import JSONDecodeError
from .env import *


app = Typer()


@app.command()
def register(
    node_name: str = Argument(..., help='Node name to register'),
    pod_id: str = Option(None, help='Pod ID to register the new node to.')
):
    """
    Creates a new node and registers it to the specified pod ID.
    If no pod ID is specified, the newly created node is registered to the default pod.
    """
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    data = json.dumps({
        "name": node_name,
        "podId": pod_id
    })
    res = requests.post(f"http://{API_HOST}:{API_PORT}/nodes", data=data, headers=headers)
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def rm(node_id: str = Argument(..., help='Node ID to remove.')):
    """
    Removes the specified node.
    [IMPORTANT] The command fails if the name does not exist or if its status is not “Idle”.
    """
    res = requests.delete(f"http://{API_HOST}:{API_PORT}/nodes/{node_id}")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def ls(
    pod_id: str = Option(None, help='Pod ID to list the nodes for.'),
    node_id: str = Option(None, help='Node ID to fetch the details of.')
):
    """
    Lists all the nodes in the specified resource pod.
    If no resource pod was specified, all nodes of the cloud system are listed.
    """
    if node_id:
        res = requests.get(f"http://{API_HOST}:{API_PORT}/nodes/{node_id}")
    else:
        res = requests.get(f"http://{API_HOST}:{API_PORT}/pods/{pod_id}/nodes") if pod_id else requests.get(f"http://{API_HOST}:{API_PORT}/nodes")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def log(node_id: str = Argument(..., help='Node ID to fetch the logs for')):
    """
    Prints out the entire log file of a specified node.
    [IMPORTANT] The command fails if the node ID does not exist.
    """
    res = requests.get(f"http://{API_HOST}:{API_PORT}/nodes/{node_id}/logs")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


if __name__ == "__main__":
    app()