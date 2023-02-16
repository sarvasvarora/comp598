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
default_task = "publish"


@init
def set_properties(project):
    project.depends_on("fastapi")
    project.depends_on("pydantic")
    project.depends_on("uvicorn")
    project.depends_on("typer[all]")
    project.depends_on("rich")
    project.depends_on("python-multipart")

@task
def run_resource_manager(project):
    sys.path.append('src/main/python')
    os.environ['API_HOST'] = "localhost"
    os.environ['API_PORT'] = "3000"
    uvicorn.run('ResourceManager.resource_manager:app', host='127.0.0.1', port=3000, log_level='info', reload=True)
