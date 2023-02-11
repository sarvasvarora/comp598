from typer import Typer, Argument, Option


app = Typer.app()


@app.command()
def launch(path_to_job: str = Argument(..., help='Path to the job to execute.')):
    """
    Launches the specified job.
    """
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    data = {
        "path": path_to_job,
        "status": "Requested",
        "jobId": -1
    }
    res = requests.post(f"http://{API_HOST}:{API_PORT}/jobs/", data=data, headers=headers)
    print(res)


@app.command()
def abort(job_id: str = Argument(..., help='Job ID to abort.')):
    """
    Aborts the specified job.
    [IMPORTANT] The command fails if the job does not exist or if it has “Completed” status.
    """
    res = requests.delete(f"http://{API_HOST}:{API_PORT}/jobs/{job_id}")
    print(res)


@app.command()
def ls():
    """
    Lists all resource pods in the main cluster.
    """
    res = requests.get(f"http://{API_HOST}:{API_PORT}/pods/")
    print(res)


@app.command()
def log():
    pass


if __name__ == "__main__":
    app()