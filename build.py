#   -*- coding: utf-8 -*-
from pybuilder.core import use_plugin, init

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
    project.depends_on("docker")