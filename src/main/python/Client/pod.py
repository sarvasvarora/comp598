from typer import Typer, Argument, Option


app = Typer.app()


@app.command()
def register(pod_name: str = Argument(..., help='Pod name to register with the cloud.')):
    """
    Registers a new pod with the specified name to the main resource cluster. 
    [IMPORTANT] Pod names must be unique.
    """
    headers = {
        "Content-Type": "application/json",
        "accept":"application/json"
    }
    data = {
        "name": pod_name
    }
    res = requests.post(f"http://{API_HOST}:{API_PORT}/pods/", data=data, headers=headers)
    print(res)


@app.command()
def rm(pod_name: str = Argument(..., help='Pod name to remove from the cloud.')):
    """
    Removes the specified pod. The command fails if there are nodes registered to this pod or if the specified pod is the default pod.
    """
    requests.delete(f"http://{API_HOST}:{API_PORT}/pods/{pod_name}")
    print(res)


@app.command()
def ls():
    pass


if __name__ == "__main__":
    app()