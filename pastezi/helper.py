import asyncio
import functools
from typing import Any, Awaitable, Callable


def make_async(f: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    @functools.wraps(f)
    async def wrapper(*args, **kwargs) -> Any:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: f(*args, **kwargs)
        )

    return wrapper
