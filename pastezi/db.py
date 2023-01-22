import asyncio
import aioredis

class Backend:
    def __init__(self):
        self.expiration = 6 * 7 * 86400  # Six weeks

    async def start(self):
        self.ns = "pastezi:"
        loop = asyncio.get_event_loop()
        self.redis = await aioredis.from_url('redis://localhost', decode_responses=True)

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
        await self.redis.hset(id, mapping=value)
        await self.redis.expire(id, self.expiration)
        return created

    async def delete(self, id):
        id = self.ns + id
        deleted = await self.redis.exists(id)
        await self.redis.delete(id)
        return deleted
