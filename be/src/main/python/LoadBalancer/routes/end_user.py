from fastapi import APIRouter, Body, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
import requests_async as requests
from datetime import datetime
from ..env import *
from ..shared_resources import *
from ..models import *
from ..status import PodStatus


router = APIRouter()


####################
# HEAVY JOB ENDPOINT
####################
@router.get("/heavy")
async def heavy_get(req: Request):
    req_arrival_time = datetime.now()
    client_host = req.client.host
    if database.get_heavy_pod_status() == PodStatus.ACTIVE:
        res = await requests.get(f"http://localhost:{HAPROXY_FRONTEND_PORT}/heavy")
        time_elapsed = res.elapsed.total_seconds()
        # log the request information
        request_monitor.log_request(
            job_type='heavy',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=time_elapsed)
        return StreamingResponse(res)  
    else:
        request_monitor.log_request(
            job_type='heavy',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=0.
        )
        return {"Pod inactive: couldn't execute request."}



@router.post("/heavy")
async def heavy(req: Request, data = Body(...)):
    req_arrival_time = datetime.now()
    client_host = req.client.host
    data = jsonable_encoder(data)
    if database.get_heavy_pod_status() == PodStatus.ACTIVE:
        res = await requests.post(f"http://localhost:{HAPROXY_FRONTEND_PORT}/heavy", json=data)
        time_elapsed = res.elapsed.total_seconds()
        # log the request information
        request_monitor.log_request(
            job_type='heavy',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=time_elapsed)
        return StreamingResponse(res)
    else:
        request_monitor.log_request(
            job_type='heavy',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=0.
        )
        return {"Pod inactive: couldn't execute request."}


#####################
# MEDIUM JOB ENDPOINT
#####################
@router.get("/medium")
async def medium_get(req: Request):
    req_arrival_time = datetime.now()
    client_host = req.client.host
    if database.get_medium_pod_status() == PodStatus.ACTIVE:
        res = await requests.get(f"http://localhost:{HAPROXY_FRONTEND_PORT}/medium")
        time_elapsed = res.elapsed.total_seconds()
        # log the request information
        request_monitor.log_request(
            job_type='medium',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=time_elapsed)
        return StreamingResponse(res)
    else:
        request_monitor.log_request(
            job_type='medium',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=0.
        )
        return {"Pod inactive: couldn't execute request."}


@router.post("/medium")
async def medium(req: Request, data = Body(...)):
    req_arrival_time = datetime.now()
    client_host = req.client.host
    data = jsonable_encoder(data)
    if database.get_medium_pod_status() == PodStatus.ACTIVE:
        res = await requests.post(f"http://localhost:{HAPROXY_FRONTEND_PORT}/medium", json=data)
        time_elapsed = res.elapsed.total_seconds()
        # log the request information
        request_monitor.log_request(
            job_type='medium',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=time_elapsed)
        return StreamingResponse(res)
    else:
        request_monitor.log_request(
            job_type='medium',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=0.
        )
        return {"Pod inactive: couldn't execute request."}


####################
# LIGHT JOB ENDPOINT
####################
@router.get("/light")
async def light_get(req: Request):
    req_arrival_time = datetime.now()
    client_host = req.client.host
    if database.get_light_pod_status() == PodStatus.ACTIVE:
        res = await requests.get(f"http://localhost:{HAPROXY_FRONTEND_PORT}/light")
        time_elapsed = res.elapsed.total_seconds()
        # log the request information
        request_monitor.log_request(
            job_type='light',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=time_elapsed)
        return StreamingResponse(res)
    else:
        request_monitor.log_request(
            job_type='light',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=0.
        )
        return {"Pod inactive: couldn't execute request."}


@router.post("/light")
async def light(req: Request, data = Body(...)):
    req_arrival_time = datetime.now()
    client_host = req.client.host
    data = jsonable_encoder(data)
    if database.get_light_pod_status() == PodStatus.ACTIVE:
        res = await requests.post(f"http://localhost:{HAPROXY_FRONTEND_PORT}/light", json=data)
        time_elapsed = res.elapsed.total_seconds()
        # log the request information
        request_monitor.log_request(
            job_type='light',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=time_elapsed)
        return StreamingResponse(res)
    else:
        request_monitor.log_request(
            job_type='light',
            client_host=client_host,
            request_arrival_time=req_arrival_time,
            response_time=0.
        )
        return {"Pod inactive: couldn't execute request."}
