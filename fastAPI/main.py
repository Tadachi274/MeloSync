from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class HeartRate(BaseModel):
    heartrate: int

@app.post("/heartrate")
async def receive_heartrate(data: HeartRate):
    print("Received:", data.dict())
    return {
    "status": "received",
    "data": data.dict()
}

# 如果你想用 uvicorn 執行：
# uvicorn filename:app --reload --port 5000