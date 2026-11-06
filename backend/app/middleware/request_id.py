import uuid
from starlette.datastructures import Headers, MutableHeaders


class RequestIdMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        supplied = Headers(scope=scope).get("x-request-id", "")
        try:
            request_id = str(uuid.UUID(supplied)) if len(supplied) <= 36 else str(uuid.uuid4())
        except ValueError:
            request_id = str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id

        async def attach(message):
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["X-Request-Id"] = request_id
            await send(message)

        await self.app(scope, receive, attach)
