from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from database import database , messages



# Initialize the FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# Connection manager class for handling WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[dict] = []

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections.append({"websocket": websocket, "username": username})
        await self.broadcast(f"{username} joined the chat")

    def disconnect(self, websocket: WebSocket):
        for connection in self.active_connections:
            if connection["websocket"] == websocket:
                username = connection["username"]
                self.active_connections.remove(connection)
                return username

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection["websocket"].send_text(message)

    async def send_private_message(self, from_username: str, to_username: str, message: str):
        for connection in self.active_connections:
            if connection["username"] == to_username:
                await connection["websocket"].send_text(f"Private from {from_username}: {message}")


manager = ConnectionManager()



# Save messages to the PostgreSQL database
async def save_message(username: str, message: str):
    query = messages.insert().values(username=username, message=message)
    await database.execute(query)

# Retrieve the message history from the PostgreSQL database
async def get_message_history():
    query = messages.select()
    return await database.fetch_all(query)

# WebSocket route for real-time chat
@app.websocket("/ws/chat/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)

    # Load message history when a new user connects
    history = await get_message_history()
    for record in history:
        await websocket.send_text(f"{record['username']}: {record['message']}")
    
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("/private"):
                _, to_username, private_message = data.split(" ", 2)
                await manager.send_private_message(username, to_username, private_message)
            else:
                await save_message(username, data)
                await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        username = manager.disconnect(websocket)
        await manager.broadcast(f"{username} left the chat")

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
