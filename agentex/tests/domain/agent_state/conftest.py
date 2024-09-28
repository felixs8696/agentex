from typing import List, Any, Dict

import pytest

from agentex.adapters.memory.port import MemoryRepository


class FakeMemoryRepo(MemoryRepository):

    def __init__(self):
        self.data = {}

    async def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    async def batch_set(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)

    async def get(self, key: str) -> Any:
        return self.data.get(key)

    async def batch_get(self, keys: List[str]) -> List[Any]:
        return [self.data.get(key) for key in keys]

    async def delete(self, key: str) -> Any:
        return self.data.pop(key, None)

    async def batch_delete(self, keys: List[str]) -> List[Any]:
        return [self.data.pop(key, None) for key in keys]

    async def publish(self, channel: str, message: str) -> None:
        pass

    async def subscribe(self, channel: str):
        pass


@pytest.fixture(scope="function")
def mock_memory_repo():
    return FakeMemoryRepo()
