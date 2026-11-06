"""Metadata-only request auditing. Never log raw paths, bodies, headers or errors."""

import json
import time
from app.core.logging import logger


class AuditMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = time.monotonic()
        status = 500

        async def capture(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, capture)
        finally:
            route = scope.get("route")
            state = scope.get("state", {})
            event = {
                "event": "http_request",
                "request_id": state.get("request_id"),
                "endpoint": getattr(route, "path", "<unmatched>"),
                "status_code": status,
                "duration_ms": round((time.monotonic() - started) * 1000, 2),
                "actor_id": state.get("actor_id"),
                "error_code": state.get("error_code"),
            }
            logger.info(json.dumps(event, separators=(",", ":")))
