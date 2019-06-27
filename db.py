import asyncio
import aioredis
import json

class Backend:
    def __init__(self):
        self.expiration = 7 * 86400.0  # A week

    async def start(self, loop):
        self.ns = "pastezi:"
        loop = asyncio.get_event_loop()
        self.redis = await aioredis.create_redis_pool('redis://localhost', minsize=5, maxsize=10, loop=loop, encoding="UTF-8")

    async def close(self):
        self.redis.close()
        await self.redis.wait_closed()

    async def __getitem__(self, id):
        id = self.ns + id
        value = await self.redis.hgetall(id) or None
        if value: await self.redis.expire(id, self.expiration)
        return value

    async def store(self, id, value):
        id = self.ns + id
        created = not await self.redis.exists(id)
        await self.redis.hmset_dict(id, value)
        await self.redis.expire(id, self.expiration)
        return created

    async def delete(self, id):
        id = self.ns + id
        deleted = await self.redis.exists(id)
        await self.redis.delete(id)
        return deleted
