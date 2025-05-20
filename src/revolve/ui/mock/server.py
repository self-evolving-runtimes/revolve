from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

server_status = "Server is not running"


class Message(BaseModel):
    message: str


@app.post("/api/start")
async def start_server():
    global server_status
    server_status = "Server is running"
    return {"message": server_status}


@app.post("/api/stop")
async def stop_server():
    global server_status
    server_status = "Server is not running"
    return {"message": server_status}


@app.post("/api/chat")
async def chat_endpoint(msg: Message):
    print(f"Received message: {msg.message}")
    # Simple echo response
    reply = f"Echo: {msg.message}"
    return {"reply": reply}


@app.get("/api/status")
async def get_status():
    return {"status": server_status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3008)

