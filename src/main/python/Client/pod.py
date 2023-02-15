from typer import Typer, Argument, Option
from rich import print, print_json
import requests
import json
from json import JSONDecodeError
from .env import *


app = Typer()


@app.command()
def register(pod_name: str = Argument(..., help='Pod name to register with the cloud.')):
    """
    Registers a new pod with the specified name to the main resource cluster. 
    [IMPORTANT] Pod names must be unique.
    """
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    data = json.dumps({
        "name": pod_name
    })
    res = requests.post(f"http://{API_HOST}:{API_PORT}/pods/", data=data, headers=headers)
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def rm(pod_id: str = Argument(..., help='Pod ID to remove from the cloud.')):
    """
    Removes the specified pod. The command fails if there are nodes registered to this pod or if the specified pod is the default pod.
    """
    res = requests.delete(f"http://{API_HOST}:{API_PORT}/pods/{pod_id}")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def ls():
    """
    Lists all resource pods in the main cluster.
    """
    res = requests.get(f"http://{API_HOST}:{API_PORT}/pods")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


if __name__ == "__main__":
    app()