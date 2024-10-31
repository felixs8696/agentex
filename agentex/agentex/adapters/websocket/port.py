from abc import ABC, abstractmethod

from fastapi import WebSocket


class WebSocketPort(ABC):
    @abstractmethod
    async def connect(self, websocket: WebSocket):
        pass

    @abstractmethod
    async def disconnect(self, websocket: WebSocket):
        pass

    @abstractmethod
    async def receive_text(self, websocket: WebSocket) -> str:
        pass

    @abstractmethod
    async def send_text(self, websocket: WebSocket, message: str):
        pass
