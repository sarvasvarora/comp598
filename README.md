# COMP 598 Cloud Application (Backend + CLI)

## Build instructions
- Clone the project and (optionally) start a python virtual environment in the project's root directory.
- Execute `pyb install` to install dependencies, build the project, and install the `cloud` CLI to interact with the cloud application.
- Available scripts and commands:
  - `source setup-env`: sets up the default environment variables to run various components of the project. By default, everything runs on localhost (127.0.0.1). The frontend runs on port 3000, the resource manager on port 8000, and the proxy on port 9000.
  - `cleanup`: to cleanup the docker containers created by the proxy. This is automatically called in the proxy if anything goes wrong, however, you may also manually call it to delete the containers.
  - `cloud`: the CLI app to interact with the cloud application. More on this later.
  - `pyb run_proxy`: runs the proxy.
  - `pyb run_resource_manager`: runs the resource manager.
- You may manually set these environment variables to change the location where components are hosted:
  - Frontend: `FRONTEND_HOST` and `FRONTEND_PORT`.
  - Resource manager: `API_HOST`, `API_PORT`, `DEFAULT_CLUSTER_NAME`, and `DEFAULT_POD_NAME`.
  - Proxy: `PROXY_HOST`, `PROXY_PORT`, and `NUM_NODES` (number of default containers to spin up when the cloud application is initialized).


## The `cloud` CLI
The `cloud` CLI is built using the `typer` Python library and exposes several commands to interact with the cloud application.
Commands are grouped into various resource groups associated with the project i.e., clusters, pods, nodes, and jobs.

For any command, you may execute `cloud [sub_command] --help` to get more info about it.

Following are some important commands:
- `cloud init`: initializes the cloud backend by provisioning the default pod and nodes. Note that it may take a little while to execute.
- `cloud node register <node_name> [--pod-id <pod_id>]`: to register a node to the (optionally) specified pod.
- `cloud node ls [-node-id <node_id>] [--pod-id <pod_id>]`: display all the nodes (or the particular node specified by the node ID) registered under the (optionally) specified pod.
- `cloud job launch <path_to_script>`: submits the script at the specified path to be executed in one of the idle nodes. If no idle node is present at the moment, the job will be executed later once a node becomes available.
- `cloud job abort <job_id>`: aborts the specified job if it has not yet completed execution. A small number of aborted jobs are stored on the cloud for future reference. Older aborted jobs are replaced by newer aborted jobs.
- `cloud job ls [--job-id <job_id>] [--aborted]`: display all the jobs (or the partiular job specified by the job ID). Note that if the aborted flag is specified, it will only display the aborted jobs.