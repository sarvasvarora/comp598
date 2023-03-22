#   -*- coding: utf-8 -*-
from pybuilder.core import use_plugin, init, task
import sys
import os
import uvicorn
import typer

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.flake8")
use_plugin("python.distutils")


name = "cloud_manager"
default_task = ["install_dependencies", "publish"]


@init
def set_properties(project):
    project.depends_on("fastapi")
    project.depends_on("pydantic")
    project.depends_on("uvicorn")
    project.depends_on("typer[all]")
    project.depends_on("rich")
    project.depends_on("python-multipart")
    project.depends_on("docker")

@task
def run_resource_manager(project):
    sys.path.append('src/main/python')
    from Client.env import API_HOST, API_PORT
    uvicorn.run('ResourceManager.resource_manager:app', host=API_HOST, port=API_PORT, log_level='info', reload=True)

@task
def run_heavy(project):
    sys.path.append('src/main/python')
    from Resource.proxy import main
    main("heavy")

@task
def run_medium(project):
    sys.path.append('src/main/python')
    from Resource.proxy import main
    main("medium")

@task
def run_light(project):
    sys.path.append('src/main/python')
    from Resource.proxy import main
    main("light")

@task
def run_load_balancer(project):
    sys.path.append('src/main/python')
    from LoadBalancer.env import LOAD_BALANCER_HOST, LOAD_BALANCER_PORT
    uvicorn.run('LoadBalancer.load_balancer:app', host=LOAD_BALANCER_HOST, port=LOAD_BALANCER_PORT, log_level='info', reload=True)
