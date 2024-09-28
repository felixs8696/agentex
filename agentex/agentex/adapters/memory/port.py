from abc import ABC, abstractmethod
from typing import Any, Annotated, Optional, Dict, List

from fastapi import Depends


class MemoryRepository(ABC):

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def batch_set(self, updates: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def batch_get(self, keys: List[str]) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def batch_delete(self, keys: List[str]) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    async def publish(self, channel: str, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, channel: str):
        raise NotImplementedError


DMemoryRepository = Annotated[Optional[MemoryRepository], Depends(MemoryRepository)]
