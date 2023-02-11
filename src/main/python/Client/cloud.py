from typer import Typer, Argument, Option
from rich import print
import requests
import os
import socket
import pod
import node
import job

# obtain the API_HOST and API_PORT env variables
API_HOST = socket.gethostbyname(os.environ.get('API_HOST')) or "10.140.17.113"
API_PORT = int(os.environ.get('API_PORT')) or 8000

# initialize the CLI app
app = Typer.app()
app.add(pod.app, name='pod')
app.add(node.app, name='node')
app.add(job.app, name='job')


@app.command()
def init():
    res = requests.get(f"http://{API_HOST}:{API_PORT}/init/")
    print(res)


@app.command()
def register():
    pass


@app.command()
def rm():
    pass


@app.command()
def launch():
    pass


@app.command()
def abort():
    pass


# run the CLI app
if __name__ == "__main__":
    app()
