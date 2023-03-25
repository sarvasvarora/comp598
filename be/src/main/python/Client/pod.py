from typer import Typer, Argument, Option
from rich import print, print_json
import requests
import json
from json import JSONDecodeError
from .env import *


app = Typer()


@app.command()
def register(
    pod_name: str = Argument(..., help='Pod name to register with the cloud.'),
    cluster_id: str = Option(None, help='Cluster ID to register the pod in.')
):
    """
    Registers a new pod with the specified name to the main resource cluster. 
    [IMPORTANT] Pod names must be unique.
    """
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    data = json.dumps({
        "name": pod_name,
        "clusterId": cluster_id
    })
    res = requests.post(f"http://{API_HOST}:{API_PORT}/pods", data=data, headers=headers)
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def rm(pod_id: str = Argument(..., help='Pod ID to remove from the cloud.')):
    """
    Removes the specified pod.
    [IMPORTANT] The command fails if there are nodes registered to this pod or if the specified pod is the default pod.
    """
    res = requests.delete(f"http://{API_HOST}:{API_PORT}/pods/{pod_id}")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)

@app.command()
def ls(
    pod_id: str = Option(None, help='Pod ID to fetch the details of.'),
    cluster_id: str = Option(None, help='Node ID to fetch the details of.')
):
    """
    Lists all resource pods in the main cluster.
    """
    if pod_id:
        res = requests.get(f"http://{API_HOST}:{API_PORT}/pods/{pod_id}") if pod_id else requests.get(f"http://{API_HOST}:{API_PORT}/pods")
    else:
        res = requests.get(f"http://{API_HOST}:{API_PORT}/clusters/{cluster_id}/pods") if cluster_id else requests.get(f"http://{API_HOST}:{API_PORT}/pods")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)

@app.command() 
def pause(pod_id: str = Argument(..., help='Pod ID to pause.')):
    req = requests.get(f"http://{API_HOST}:{API_PORT}/nodes")
    for i in range(len(req.json()['Nodes'])):
        data = list(req.json()['Nodes'][i].values())[0]
        nodeId = list(req.json()['Nodes'][i].keys())[0]
        if data['podId'] == pod_id and data['status'] == 'online':
            res = requests.delete(f"http://{API_HOST}:{API_PORT}/nodes/{nodeId}")
            try:
                print_json(data=res.json())
            except JSONDecodeError:
                print(res.text)
    req = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/pods/{pod_id}", json={'status': 'inactive'})
    try:
        print_json(data=req.json())
    except JSONDecodeError:
        print(req.text)

@app.command()
def resume(pod_id: str = Argument(..., help='Pod ID to resume.')):
    req = requests.post(f"http://{LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT}/cloud/pods/{pod_id}", json={'status': 'active'})
    try:
        print_json(data=req.json())
    except JSONDecodeError:
        print(req.text)


if __name__ == "__main__":
    app()