"""Bound actual request bytes, including chunked and misleading-length requests."""

from starlette.datastructures import Headers
from app.middleware.responses import error_response


class BodyLimitMiddleware:
    def __init__(self, app, max_body_bytes=1024 * 1024):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        lengths = headers.getlist("content-length")
        if lengths:
            try:
                if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
                    raise ValueError
                length = int(lengths[0])
            except ValueError:
                return await error_response(scope, 400, "INVALID_CONTENT_LENGTH", "Invalid Content-Length header.")(scope, receive, send)
            if length > self.max_body_bytes:
                return await self.too_large(scope, receive, send)
        encoding = headers.get("content-encoding", "identity").lower()
        if encoding != "identity":
            return await error_response(scope, 415, "UNSUPPORTED_ENCODING", "Compressed request bodies are not supported.")(scope, receive, send)

        # Read before dispatch so no route can write data before an oversized tail arrives.
        body = bytearray()
        total = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            total += len(message.get("body", b""))
            if total > self.max_body_bytes:
                return await self.too_large(scope, receive, send)
            # Coalesce chunks to avoid unbounded per-message overhead for tiny chunks.
            body.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break
        body = bytes(body)
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

    async def too_large(self, scope, receive, send):
        await error_response(scope, 413, "REQUEST_TOO_LARGE", "Request body exceeds the allowed size.")(scope, receive, send)
