from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from .env import *
from .database import Database
from .routes import cloud, end_user
from .health_checker import HealthChecker
from .request_monitor import RequestMonitor


# initialize the FastAPI app
app = FastAPI()


# enable CORS
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# run the health checker
health_checker.run()


###############
# ROOT ENDPOINT
###############
@app.get("/")
async def root():
    return {"Hello, World!"}


#################
# CLOUD ENDPOINTS
#################
app.include_router(
    cloud.router,
    prefix="/cloud"
)


####################
# END USER ENDPOINTS
####################
app.include_router(
    end_user.router,
    prefix="/api"
)