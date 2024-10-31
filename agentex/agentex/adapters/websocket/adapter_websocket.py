from fastapi import WebSocket

from agentex.adapters.websocket.port import WebSocketPort


class WebSocketManager(WebSocketPort):
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def receive_text(self, websocket: WebSocket) -> str:
        return await websocket.receive_text()

    async def send_text(self, websocket: WebSocket, message: str):
        await websocket.send_text(message)
