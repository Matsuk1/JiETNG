"""异步客户端 / Async client（与 sync 客户端 API 形态完全一致，方法都 async）。"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Tuple

import httpx

from ._http import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    _attachment_filename,
    _binary_response,
    _build_headers,
    _check_response,
)


class _BaseAsyncResource:
    __slots__ = ("_client",)

    def __init__(self, client: "AsyncJiETNGClient"):
        self._client = client


class AsyncUsersResource(_BaseAsyncResource):
    async def list(self) -> dict:
        return await self._client._request("GET", "/users")

    async def get(self, user_id: str) -> dict:
        return await self._client._request("GET", f"/users/{user_id}")

    async def create(self, **fields: Any) -> dict:
        return await self._client._request("POST", "/users", json=fields)

    async def delete(self, user_id: str) -> dict:
        return await self._client._request("DELETE", f"/users/{user_id}")

    async def trigger_sync(self, user_id: str) -> dict:
        return await self._client._request("POST", f"/users/{user_id}/tasks")

    async def get_rebind_url(self, user_id: str) -> dict:
        return await self._client._request("GET", f"/users/{user_id}/rebind-url")

    async def get_settings_url(self, user_id: str) -> dict:
        return await self._client._request("GET", f"/users/{user_id}/settings-url")

    async def bind(self, user_id: str, **fields: Any) -> dict:
        return await self._client._request("POST", f"/users/{user_id}/bind", json=fields)

    async def update_bind(self, user_id: str, **fields: Any) -> dict:
        return await self._client._request("PUT", f"/users/{user_id}/bind", json=fields)


class AsyncPermissionsResource(_BaseAsyncResource):
    async def request(self, user_id: str, requester_name: Optional[str] = None) -> dict:
        body = {"requester_name": requester_name} if requester_name else {}
        return await self._client._request("POST", f"/users/{user_id}/permissions", json=body)

    async def list_requests(self, user_id: str) -> dict:
        return await self._client._request("GET", f"/users/{user_id}/permissions/requests")

    async def accept(self, user_id: str, request_id: str) -> dict:
        return await self._client._request(
            "PATCH",
            f"/users/{user_id}/permissions/requests/{request_id}",
            json={"action": "accept"},
        )

    async def reject(self, user_id: str, request_id: str) -> dict:
        return await self._client._request(
            "PATCH",
            f"/users/{user_id}/permissions/requests/{request_id}",
            json={"action": "reject"},
        )

    async def revoke(self, user_id: str, token_id: str) -> dict:
        return await self._client._request("DELETE", f"/users/{user_id}/permissions/{token_id}")

    async def revoke_self(self, user_id: str) -> dict:
        return await self._client._request("DELETE", f"/users/{user_id}/permissions/self")


class AsyncSongsResource(_BaseAsyncResource):
    async def search(
        self,
        q: str,
        ver: str = "jp",
        max_results: int = 6,
        user_id: Optional[str] = None,
    ) -> dict:
        params = {"q": q, "ver": ver, "max_results": max_results}
        if user_id:
            params["user_id"] = user_id
        return await self._client._request("GET", "/songs/search", params=params)

    async def info(self, song_id: str) -> bytes:
        return await self._client._request("GET", f"/songs/{song_id}/image", binary=True)


class AsyncTasksResource(_BaseAsyncResource):
    async def get(self, task_id: str) -> dict:
        return await self._client._request("GET", f"/tasks/{task_id}")


class AsyncVersionsResource(_BaseAsyncResource):
    async def list(self) -> dict:
        return await self._client._request("GET", "/versions")


class AsyncDxdataResource(_BaseAsyncResource):
    async def get(self) -> dict:
        return await self._client._request("GET", "/dxdata")


class AsyncImagesResource(_BaseAsyncResource):
    async def user_song(self, user_id: str, song_id: str) -> bytes:
        return await self._client._request(
            "GET", f"/users/{user_id}/songs/{song_id}/image", binary=True,
        )

    async def records(self, user_id: str, command: str = "b50") -> bytes:
        return await self._client._request(
            "GET", f"/users/{user_id}/image",
            params={"command": command}, binary=True,
        )

    async def plate(self, user_id: str, title: str, filter_mode: Optional[str] = None) -> bytes:
        params: dict = {"title": title}
        if filter_mode:
            params["filter"] = filter_mode
        return await self._client._request(
            "GET", f"/users/{user_id}/plate", params=params, binary=True,
        )

    async def achievement(
        self,
        user_id: str,
        level: str,
        rank: Optional[str] = None,
        filter_mode: Optional[str] = None,
    ) -> bytes:
        params: dict = {"level": level}
        if rank:
            params["rank"] = rank
        if filter_mode:
            params["filter"] = filter_mode
        return await self._client._request(
            "GET", f"/users/{user_id}/achievement", params=params, binary=True,
        )


class AsyncExportsResource(_BaseAsyncResource):
    async def download(self, user_id: str, fmt: str = "json") -> Tuple[bytes, Optional[str]]:
        return await self._client._request_with_filename(
            "GET", f"/users/{user_id}/export", params={"fmt": fmt},
        )

    async def save(self, user_id: str, fmt: str = "json", path: Optional[str] = None) -> str:
        content, suggested = await self.download(user_id, fmt=fmt)
        target = path or suggested or f"jietng-{user_id}.{fmt}"
        with open(target, "wb") as f:
            f.write(content)
        return target


# ============================================================
# 主 async client
# ============================================================

class AsyncJiETNGClient:
    """异步 JiETNG API 客户端。

    Example::

        import asyncio
        from jietng import AsyncJiETNGClient

        async def main():
            async with AsyncJiETNGClient(token="your_token") as client:
                users = await client.users.list()
                png = await client.images.records("U123", command="b50")

        asyncio.run(main())
    """

    def __init__(
        self,
        token: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        extra_headers: Optional[Mapping[str, str]] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        if not token:
            raise ValueError("token is required")
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._headers = _build_headers(token, extra_headers)
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=timeout,
            transport=transport,
        )

        self.users = AsyncUsersResource(self)
        self.permissions = AsyncPermissionsResource(self)
        self.songs = AsyncSongsResource(self)
        self.tasks = AsyncTasksResource(self)
        self.versions = AsyncVersionsResource(self)
        self.dxdata = AsyncDxdataResource(self)
        self.images = AsyncImagesResource(self)
        self.exports = AsyncExportsResource(self)

    async def __aenter__(self) -> "AsyncJiETNGClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.aclose()

    async def _request(self, method: str, path: str, *, binary: bool = False, **kwargs: Any) -> Any:
        resp = await self._http.request(method, path, **kwargs)
        if binary:
            return _binary_response(resp)
        return _check_response(resp)

    async def _request_with_filename(
        self, method: str, path: str, **kwargs: Any,
    ) -> Tuple[bytes, Optional[str]]:
        resp = await self._http.request(method, path, **kwargs)
        content = _binary_response(resp)
        return content, _attachment_filename(resp)
