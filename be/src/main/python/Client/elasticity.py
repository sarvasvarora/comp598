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

if __name__ == "__main__":
    app()