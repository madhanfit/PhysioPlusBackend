import time
from fastapi import FastAPI, Request
    
app = FastAPI()
    
@app.get("/ping")
def ping(request: dict):
    req_info = request['Hello']
    print(req_info)
    print("Hello")
    time.sleep(5)
    print("bye")
    return {"ping": "pong!"}