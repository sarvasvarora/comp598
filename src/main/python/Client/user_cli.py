import json
import requests


# RM is running on 'winter2023-comp598-group05-01.cs.mcgill.ca'
api_host = '10.140.17.113'
api_port = '8000'

# Calls the RestAPI with the right parameters for each cli command
def execute_cmd(cmd):
    if cmd.strip() == "cloud init":
        res = requests.get(f'http://{api_host}:{api_port}/init/')
        print(res.text)
        return res
    elif (cmd.strip()).startswith('cloud pod register'):
        pod_name = ((cmd.strip()).split())[3]
        if not pod_name:
            print ('POD_NAME required for registering a pod')
            return
        res = requests.post(f'http://{api_host}:{api_port}/pods/', json={'name':pod_name}, headers={"Content-Type": "application/json", "accept":"application/json"})
        print(res.text)
        return res
    elif (cmd.strip()).startswith('cloud pod rm'):
        pod_name = ((cmd.strip()).split())[3]
        if not pod_name:
            print ('POD_NAME required for removing a pod')
            return
        res = requests.delete(f'http://{api_host}:{api_port}/pods/{pod_name}')
        print(res.text)
        return res
    elif (cmd.strip()).startswith('cloud register'):
        s = (cmd.strip()).split()
        node_name = s[2]
        pod_name = 'default'

        if not node_name:
            print ('NODE_NAME required for registering a node')
            return
        
        # Check if user specified pod name
        if len(s) == 4:
            pod_name = s[3]
        
        res = requests.post(f'http://{api_host}:{api_port}/nodes/', json={'name': node_name, 'pod_name': pod_name}, headers={"Content-Type": "application/json", "accept":"application/json"})
        print(res)
        return res
    elif (cmd.strip()).startswith('cloud rm'):
        node_name = ((cmd.strip()).split())[2]
        if not node_name:
            print ('NODE_NAME required for removing a node')
            return
        res = requests.delete(f'http://{api_host}:{api_port}/nodes/{node_name}')
        print(res)
        return res
    elif (cmd.strip()).startswith('cloud launch'):
        path_to_job = ((cmd.strip()).split())[2]
        if not path_to_job:
            print ('PATH_TO_JOB required for launching a job')
            return
        files = {'file': open(path_to_job, 'rb')}

        # Job status 'Requested' and jobId '-1' is used to demonstrate that the request is sent to the api
        res = requests.post(f'http://{api_host}:{api_port}/jobs/', files=files)
        print(res.text)
        return res
    elif (cmd.strip()).startswith('cloud abort'):
        job_id = ((cmd.strip()).split())[2]
        if not job_id:
            print ('JOB_ID required for aborting a job')
            return
        res = requests.delete(f'http://{api_host}:{api_port}/jobs/{job_id}')
        print(res.text)
        return res
    else:
        print("Wrong input! Please use help command to see the format of the supported commands")

# Prints out the user cli manual
def print_help():
    print('{:35s} {:50s}'.format("cloud init","Initializes the main resource cluster. All cloud services are setup"))
    print('{:35s} {:50s}'.format("cloud pod register POD_NAME","Registers a new pod with the specified name to the main resource cluster"))
    print('{:35s} {:50s}'.format("cloud pod rm POD_NAME","Removes the specified pod"))
    print('{:35s} {:50s}'.format("cloud register NODE_NAME [POD_ID]","Creates a new node and registers it to the specified pod ID"))
    print('{:35s} {:50s}'.format("cloud rm NODE_NAME","Removes the specified node"))
    print('{:35s} {:50s}'.format("cloud launch PATH_TO_JOB","Launches a specified job"))
    print('{:35s} {:50s}'.format("cloud abort JOB_ID","Aborts the specified job"))

def main():

    # The main loop for processing user commands
    while True:
        command = input("$ ")
        if command == "exit":
            break
        elif command == "help":
            print_help()
        else:
            execute_cmd(command)

if __name__ == "__main__":
    main()