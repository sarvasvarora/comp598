import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder


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


###############
# ROOT ENDPOINT
###############
@app.get("/")
async def root():
    time.sleep(0.1)
    return {"Hello, World!"}