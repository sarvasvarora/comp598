from typer import Typer, Argument, Option
from rich import print, print_json
import ast
import requests
import json
import os
from json import JSONDecodeError
from .env import *


app = Typer()

@app.command()
def lower_threshold(pod_id: str = Argument(..., help='Pod_id to set the utilization threshold on.'), value: str = Argument(..., help='String formattted dictionary containing the following keys: cpu and memory.')):
    """
    Sets a lower threshold on the cpu and memory utilization of the nodes in the specified pod. 
    """
    res = requests.post(f"http://{API_HOST}:{API_PORT}/elasticity/lower/{pod_id}/{value}")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)

@app.command()
def upper_threshold(pod_id: str = Argument(..., help='Pod_id to set the utilization threshold on.'), value: str = Argument(..., help='String formattted dictionary containing the following keys: cpu and memory.')):
    """
    Sets a lower threshold on the cpu and memory utilization of the nodes in the specified pod. 
    """
    res = requests.post(f"http://{API_HOST}:{API_PORT}/elasticity/upper/{pod_id}/{value}")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)

@app.command()
def enable(pod_id: str = Argument(..., help='Pod_id to activate elasticity on.'), lower_size: str = Argument(..., help='The lower limit on the number of nodes in the pod.'), upper_size: str = Argument(..., help='The upper limit on the number of nodes in the pod.')):
    """
    Activates elasticity manager on the specified pod_id with the input lower and upper node sizes. 
    """
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    data = json.dumps({
        "podId": pod_id,
        "lower_size": lower_size,
        "upper_size": upper_size
    })

    res = requests.post(f"http://{API_HOST}:{API_PORT}/elasticity/enable", data=data, headers=headers)
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)

@app.command()
def disable(pod_id: str = Argument(..., help='Pod_id to disable elasticity on.')):
    """
    Disables elasticity on the specified pod.
    """

    res = requests.get(f"http://{API_HOST}:{API_PORT}/elasticity/disable/{pod_id}")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)

if __name__ == "__main__":
    app()