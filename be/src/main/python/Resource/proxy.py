import socket, sys, os
from threading import Thread
import docker
from datetime import datetime
import json
import subprocess
import shutil
from .env import *

"""
TODO DEV NOTES
    - [DONE] Initial node/container names of the form {default_pod_name}_{node_number/ID}
    - Create more helper functions and modularize the proxy program.
    - Use IDs instead of names (also applies to the first point - change it later).
    - Name containers in the form {pod_id}_{node_id} as obtained from the RM.
    - Have a CLI function (and backend functionality) to shut down and/or reset the cloud (???)
    - (For future development) Integrate the use of cluster ID in node abstraction.
    - (For future development) cache job log in the database (once returned) so that it can be made available to the client even if the node has been deleted
    - (For future development) (Design decision) Have a queue for completed jobs similar to aborted jobs. When a job has been completed, remove it from the main job list/dict and put it into this queue. This will prevent memory overload in case of a large number of jobs. A downside is that completed jobs would no longer be available to view.
"""

# Listening port and the buffer size to get client data
docker_client = docker.from_env()
idle_containers = []
in_use_containers = []

def main():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Socket initialized")
        s.bind(('', PROXY_PORT))
        print("Socket binded successfully")
        # TODO what should be the max_connections?
        s.listen(4) # Max connections of 4
    except Exception as e: 
        print("Error occured while initializing the socket" + str(e))
        sys.exit(1)

    # Creating 'jobs' directory for storing job files 
    os.mkdir(f"{ROOT_DIR}/jobs", mode = 0o777)

    while True:
        try:
            clntConnection, clntAddress = s.accept()
            # clntConnection.settimeout(120)
            print("Connection from: " + str(clntAddress))
            # Starting a thread to handle the incoming request
            Thread(target = processConnection, args = (clntConnection, clntAddress)).start()
        except: 
            s.close()
            cleanup()
            print('Exitting proxy server')
            sys.exit(1)

def processConnection(clntConnection, clntAddress):
    while True:
        try:
            # Should be blocking
            clntData = json.loads(clntConnection.recv(8192).decode('utf-8'))
            if clntData['cmd'] == 'init':
                # Create 50 docker containers as vms under the default cluster and pod
                print("Started creating containers ...")
                # TODO The number of containers to initialize should be configured
                for i in range(NUM_NODES):
                    d_name = f"{clntData['defaultPodName']}_node_{i}"
                    c = docker_client.containers.run("alpine", name=d_name, detach=True, tty=True, volumes={f"{ROOT_DIR}/jobs" : {'bind': '/mnt/vol1', 'mode': 'ro'}})
                    idle_containers.append(c)
                print("Successfully made all containers")
                message2send = {'timestamp':datetime.now(), 'status': 200}
                clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "node register":
                container = findIdleContainer(clntData['podName'])
                if container:
                    container.rename(clntData['nodeName'])
                    container.reload()
                    print(f"Renamed container to {container.name}")
                    if 'cpu' in clntData and clntData['cpu']:
                        print('CPU update needed')
                        container.update(cpu_shares=clntData['cpu'])
                    if 'memory' in clntData and clntData['memory']:
                        print('Memory update needed')
                        container.update(mem_limit=clntData['memory'])
                    if 'storage' in clntData and clntData['storage']:
                        # TODO Not an easy short way to limit storage per container 
                        print('Storage update needed')
                    message2send = {'nodeName': container.name, 'nodeStatus': container.status, 'timestamp':datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node under the podname {clntData['podName']}")
                    message2send = {'timestamp':datetime.now(), 'status': 400}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "node rm":
                container = docker_client.containers.get(clntData['nodeName'])
                if container:
                    new_name = clntData['podName'] + "_rm_" + clntData['nodeName']
                    container.rename(new_name)
                    container.reload()
                    print(f"Renamed container to {container.name}")
                    message2send = {'nodeName': container.name, 'node_status': container.status, 'timestamp':datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node named {clntData['nodeName']} to be removed")
                    message2send = {'timestamp':datetime.now(), 'status': 400}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "job launch":
                container = docker_client.containers.get(clntData['nodeName'])
                if container:
                    jobFile = open(f"{ROOT_DIR}/jobs/{clntData['jobId']}.sh", "w+")
                    jobFile.write(clntData['content'])
                    jobFile.close()
                    os.chmod(f"{ROOT_DIR}/jobs/{clntData['jobId']}.sh", 777)
                    output = container.exec_run(f"sh -c 'mkdir -p logs && cd /mnt/vol1 && ./{clntData['jobId']}.sh >> /logs/{clntData['jobId']}.log && cd ~'", stderr=True, stdout=True)
                    # TODO Add support for getting and storing pid of the launched job 
                    print(output)
                    message2send = {'nodeName': container.name, 'node_status': container.status, 'timestamp':datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node named {clntData['nodeName']} to launch the job")
                    message2send = {'timestamp':datetime.now(), 'status': 400, 'message':f"No node named {clntData['nodeName']} to launch the job"}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "job log":
                container = docker_client.containers.get(clntData['nodeName'])
                if container:
                    output = container.exec_run(f"sh -c 'cd logs && cat {clntData['jobId']}.log && cd ~'", stderr=True, stdout=True)
                    message2send = {'log': output.output.decode('utf-8'), 'timestamp': datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node named {clntData['nodeName']} to get the log")
                    message2send = {'timestamp':datetime.now(), 'status': 400, 'message':f"No node named {clntData['nodeName']} to get the log"}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "node log":
                container = docker_client.containers.get(clntData['nodeName'])
                if container:
                    output = container.exec_run(f"sh -c 'cd logs && cat *.log && cd ~'", stderr=True, stdout=True)
                    message2send = {'log': output.output.decode('utf-8'), 'timestamp': datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node named {clntData['nodeName']} to get the log")
                    message2send = {'timestamp':datetime.now(), 'status': 400, 'message':f"No node named {clntData['nodeName']} to get the log"}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
        except Exception as e:
            clntConnection.close()
            cleanup()
            print("Closed collection with client.")
            print(str(e))
            break

def findIdleContainer(pod_name):
    for c in idle_containers:
        if c.name.startswith(pod_name):
            return c
    else:
        return None

def cleanup():
    # Run the cleanup script 
    print(subprocess.run(["cleanup"], shell=True))

    # Deleting the old jobs folder
    shutil.rmtree(f"{ROOT_DIR}/jobs", ignore_errors=False, onerror=None)

if __name__ == '__main__':
    main()