"""Helpers shared by the isolated test modules."""
import asyncio
from urllib.parse import urlencode

from starlette.requests import Request


def form_request(token: str, origin: str | None = None) -> Request:
    """Build the POST request that the email-link confirmation page submits."""
    body = urlencode({"token": token}).encode()
    headers = [(b"content-type", b"application/x-www-form-urlencoded")]
    if origin is not None:
        headers.append((b"origin", origin.encode()))

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {"type": "http", "method": "POST", "path": "/", "headers": headers,
             "client": ("127.0.0.1", 50000), "server": ("testserver", 80), "scheme": "http",
             "query_string": b"", "root_path": ""}
    return Request(scope, receive)


def run(coroutine):
    return asyncio.run(coroutine)
