from typer import Typer, Argument, Option


app = Typer.app()


@app.command()
def register(
    node_name: str = Argument(..., help='Node name to register'),
    pod_name: str = Option('default', help='Pod name to register the new node to.')
):
    """
    Creates a new node and registers it to the specified pod ID.
    If no pod ID is specified, the newly created node is registered to the default pod.
    """
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    data = {
        "name": node_name,
        "pod_name": pod_name,
    }
    res = requests.post(f"http://{API_HOST}:{API_PORT}/nodes/", data=data, headers=headers)
    print(res)


@app.command()
def rm(node_name: str = Argument(..., help='Node name to remove.')):
    """
    Removes the specified node.
    [IMPORTANT] The command fails if the name does not exist or if its status is not “Idle”.
    """
    requests.delete(f"http://{API_HOST}:{API_PORT}/nodes/{node_name}")
    print(res)


@app.command()
def ls():
    pass


@app.command()
def log():
    pass


if __name__ == "__main__":
    app()