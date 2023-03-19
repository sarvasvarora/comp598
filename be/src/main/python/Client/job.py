from typer import Typer, Argument, Option
from rich import print, print_json
import requests
import json
import os
from json import JSONDecodeError
from .env import *


app = Typer()


@app.command()
def launch(path_to_job: str = Argument(..., help='Path to the job to execute.')):
    """
    Launches the specified job.
    """
    job = json.dumps({
        "filename": os.path.basename(path_to_job)
    })
    data = {
        "job": job
    }
    file = {
        "job_file": open(path_to_job, 'rb')
    }
    res = requests.post(f"http://{API_HOST}:{API_PORT}/jobs", data=data, files=file)
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def abort(job_id: str = Argument(..., help='Job ID to abort.')):
    """
    Aborts the specified job.
    [IMPORTANT] The command fails if the job does not exist or if it has “Completed” status.
    """
    res = requests.delete(f"http://{API_HOST}:{API_PORT}/jobs/{job_id}")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def ls(
    job_id: str = Option(None, help='Job ID to fetch details about'),
    aborted: bool = Option(False, help='Get aborted jobs.')
):
    """
    Lists all resource pods in the main cluster.
    """
    if not aborted:
        res = requests.get(f"http://{API_HOST}:{API_PORT}/jobs/{job_id}") if job_id else requests.get(f"http://{API_HOST}:{API_PORT}/jobs")
    else:
        res = requests.get(f"http://{API_HOST}:{API_PORT}/jobs/aborted")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


@app.command()
def log(job_id: str = Argument(..., help='Job ID to fetch the logs for.')):
    """
    Prints out the specified job's logs.
    [IMPORTANT] The command fails if the job ID does not exist or if the job has not yet completed execution.
    """
    res = requests.get(f"http://{API_HOST}:{API_PORT}/jobs/{job_id}/logs")
    try:
        print_json(data=res.json())
    except JSONDecodeError:
        print(res.text)


if __name__ == "__main__":
    app()