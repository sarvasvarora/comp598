from fastapi import APIRouter, Body, Request
from fastapi.encoders import jsonable_encoder
import requests_async as requests
from datetime import datetime
from ..env import *
from ..shared_resources import *
from ..models import *


router = APIRouter()


####################
# HEAVY JOB ENDPOINT
####################
@router.post("/heavy")
async def heavy(req: Request, data = Body(...)):
    req_arrival_time = datetime.now()
    client_host = req.client.host
    data = jsonable_encoder(data)
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    res = await requests.post(f"localhost:{HAPROXY_FRONTEND_PORT}/heavy", data=data, headers=headers)
    time_elapsed = res.elapsed.total_seconds()
    # log the request information
    request_monitor.log_request(
        job_type='heavy',
        client_host=client_host,
        request_arrival_time=req_arrival_time,
        time_elapsed=time_elapsed)
    return res


#####################
# MEDIUM JOB ENDPOINT
#####################
@router.post("/medium")
async def medium(req: Request, data = Body(...)):
    req_arrival_time = datetime.now()
    client_host = req.client.host
    data = jsonable_encoder(data)
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    res = await requests.post(f"localhost:{HAPROXY_FRONTEND_PORT}/medium", data=data, headers=headers)
    time_elapsed = res.elapsed.total_seconds()
    # log the request information
    request_monitor.log_request(
        job_type='medium',
        client_host=client_host,
        request_arrival_time=req_arrival_time,
        time_elapsed=time_elapsed)
    return res


####################
# LIGHT JOB ENDPOINT
####################
@router.post("/light")
async def light(req: Request, data = Body(...)):
    req_arrival_time = datetime.now()
    client_host = req.client.host
    data = jsonable_encoder(data)
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    res = await requests.post(f"localhost:{HAPROXY_FRONTEND_PORT}/light", data=data, headers=headers)
    time_elapsed = res.elapsed.total_seconds()
    # log the request information
    request_monitor.log_request(
        job_type='light',
        client_host=client_host,
        request_arrival_time=req_arrival_time,
        time_elapsed=time_elapsed)
    return res
