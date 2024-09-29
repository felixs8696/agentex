from typing import Any, Annotated, Optional, List, Dict

import redis.asyncio as redis
from fastapi import Depends

from agentex.adapters.memory.port import MemoryRepository


class RedisRepository(MemoryRepository):
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def set(self, key: str, value: Any) -> None:
        return await self.redis.set(key, value)

    async def batch_set(self, updates: Dict[str, Any]) -> None:
        return await self.redis.mset(updates)

    async def get(self, key: str) -> Any:
        return await self.redis.get(key)

    async def batch_get(self, keys: List[str]) -> List[Any]:
        return await self.redis.mget(keys)

    async def delete(self, key: str) -> Any:
        return await self.redis.delete(key)

    async def batch_delete(self, keys: List[str]) -> List[Any]:
        return await self.redis.delete(*keys)

    async def publish(self, channel: str, message: str) -> None:
        await self.redis.publish(channel, message)

    async def subscribe(self, channel: str):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


DRedisRepository = Annotated[Optional[RedisRepository], Depends(RedisRepository)]
