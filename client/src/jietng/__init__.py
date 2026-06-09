"""jietng — Python SDK for the JiETNG maimai DX score management API.

Quick start::

    from jietng import JiETNGClient

    client = JiETNGClient(token="your_token_here")
    users = client.users.list()
    b50_png = client.images.records("U1234567890", command="b50")

Async usage::

    import asyncio
    from jietng import AsyncJiETNGClient

    async def main():
        async with AsyncJiETNGClient(token="your_token_here") as client:
            png = await client.images.records("U1234567890", command="b50")

    asyncio.run(main())

See https://jietng.matsuk1.com/developer-api for API details and how to
obtain an access token.
"""

__version__ = "0.1.0"

from .client import JiETNGClient
from .async_client import AsyncJiETNGClient
from .exceptions import (
    APIError,
    AuthenticationError,
    JiETNGError,
    NotFoundError,
    PermissionDeniedError,
    QueueFullError,
    RateLimitedError,
    ServerError,
    ValidationError,
)

__all__ = [
    "__version__",
    "JiETNGClient",
    "AsyncJiETNGClient",
    "JiETNGError",
    "APIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ValidationError",
    "RateLimitedError",
    "ServerError",
    "QueueFullError",
]
