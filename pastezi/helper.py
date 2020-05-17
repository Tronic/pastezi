import asyncio
import functools

def make_async(f):
    @functools.wraps(f)
    async def wrapper(*args, **kwargs):
        return await asyncio.get_event_loop().run_in_executor(None, lambda: f(*args, **kwargs))
    return wrapper
