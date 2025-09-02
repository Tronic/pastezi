from typing import Any, Dict, Optional

from redis import asyncio as aioredis


class Backend:
    expiration: int
    ns: str
    redis: Optional[aioredis.Redis]

    def __init__(self):
        self.expiration = 365 * 86400  # One year
        self.ns = "pastezi:"
        self.redis = None

    async def start(self) -> None:
        self.redis = await aioredis.from_url("redis://localhost", decode_responses=True)

    async def __getitem__(self, id: str) -> Optional[Dict[str, Any]]:
        assert self.redis is not None
        id = self.ns + id
        value = await self.redis.hgetall(id) or None  # type: ignore[awaitable]
        if value:
            await self.redis.expire(id, self.expiration)
        return value

    async def store(self, id: str, value: Dict[str, Any]) -> bool:
        assert self.redis is not None
        id = self.ns + id
        created = not await self.redis.exists(id)
        await self.redis.hset(id, mapping=value)  # type: ignore[awaitable]
        await self.redis.expire(id, self.expiration)
        return created

    async def delete(self, id: str) -> bool:
        assert self.redis is not None
        id = self.ns + id
        deleted = await self.redis.exists(id)
        await self.redis.delete(id)
        return deleted
