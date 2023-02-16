import socket, sys, os
from threading import Thread
import docker
from datetime import datetime
import json
import subprocess
import shutil

# Listening port and the buffer size to get client data

port = 8000 
buffer_size = 8192
docker_client = docker.from_env()
idle_containers = []
in_use_containers = []

def main():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Socket initialized")
        s.bind(('', port))
        print("Socket binded successfully")
        # TODO what should be the max_connections?
        s.listen(4) # Max connections of 4
    except Exception as e: 
        print("Error occured while initializing the socket" + str(e))
        sys.exit(1)

    # Creating 'jobs' directory for storing job files 
    os.mkdir("./jobs", mode = 0o777)

    while True:
        try:
            clntConnection, clntAddress = s.accept()
            clntConnection.settimeout(120)
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
                print("Sratarted creating containers ...")
                # TODO The number of containers to initialize should be configured
                for i in range(2):
                    d_name = f"default_{i}"
                    c = docker_client.containers.run("alpine", name=d_name, detach=True, tty=True, volumes={'/home/comp598-user/comp598/src/main/python/Resource/jobs' : {'bind': '/mnt/vol1', 'mode': 'ro'}})
                    idle_containers.append(c)
                print("Successfully made all containers")
                message2send = {'timestamp':datetime.now(), 'status': 200}
                clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "node register":
                container = findIdleContainer(clntData['pod_name'])
                if container:
                    container.rename(clntData['node_name'])
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
                    message2send = {'node_name': container.name, 'node_status': container.status, 'timestamp':datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node under the podname {pod_name}")
                    message2send = {'timestamp':datetime.now(), 'status': 400}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "node rm":
                container = docker_client.containers.get(clntData['node_name'])
                if container:
                    new_name = clntData['pod_name'] + "_rm_" + clntData['node_name']
                    container.rename(new_name)
                    container.reload()
                    print(f"Renamed container to {container.name}")
                    message2send = {'node_name': container.name, 'node_status': container.status, 'timestamp':datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node named {node_name} to be removed")
                    message2send = {'timestamp':datetime.now(), 'status': 400}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "job launch":
                container = docker_client.containers.get(clntData['node_name'])
                if container:
                    jobFile = open(f"jobs/job_{clntData['job_id']}.sh", "w+")
                    jobFile.write(clntData['file'])
                    jobFile.close()
                    os.chmod(f"jobs/job_{clntData['job_id']}.sh", 777)
                    output = container.exec_run(f"sh -c 'mkdir -p logs && cd /mnt/vol1 && ./job_{clntData['job_id']}.sh >> /logs/job_{clntData['job_id']}.log && cd ~'", stderr=True, stdout=True)
                    # TODO Add support for getting and storing pid of the launched job 
                    print(output)
                    message2send = {'node_name': container.name, 'node_status': container.status, 'timestamp':datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node named {node_name} to launch the job")
                    message2send = {'timestamp':datetime.now(), 'status': 400, 'message':f"No node named {node_name} to launch the job"}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "job log":
                container = docker_client.containers.get(clntData['node_name'])
                if container:
                    output = container.exec_run(f"sh -c 'cd logs && cat job_{clntData['job_id']}.log && cd ~'", stderr=True, stdout=True)
                    message2send = {'log': output.output.decode('utf-8'), 'timestamp': datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node named {node_name} to get the log")
                    message2send = {'timestamp':datetime.now(), 'status': 400, 'message':f"No node named {node_name} to get the log"}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
            elif clntData['cmd'] == "node log":
                container = docker_client.containers.get(clntData['node_name'])
                if container:
                    output = container.exec_run(f"sh -c 'cd logs && cat *.log && cd ~'", stderr=True, stdout=True)
                    message2send = {'log': output.output.decode('utf-8'), 'timestamp': datetime.now(), 'status': 200}
                    clntConnection.send(json.dumps(message2send, default=str).encode('utf-8'))
                else:
                    print(f"No node named {node_name} to get the log")
                    message2send = {'timestamp':datetime.now(), 'status': 400, 'message':f"No node named {node_name} to get the log"}
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
    print(subprocess.run(["./cleanup.sh"], shell=True))

    # Deleting the old jobs folder
    shutil.rmtree("./jobs", ignore_errors=False, onerror=None)

if __name__ == '__main__':
    main()