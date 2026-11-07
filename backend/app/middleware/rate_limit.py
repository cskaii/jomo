"""Single-process MVP limits. Identities are assigned only after authentication."""

import math
import time
from collections import deque
from threading import Lock

from fastapi import HTTPException
from starlette.requests import Request
from app.middleware.responses import error_response


class SlidingWindowLimiter:
    def __init__(self, clock=time.monotonic, max_keys=10000):
        self.clock = clock
        self.max_keys = max_keys
        self.buckets = {}
        self.lock = Lock()

    def check(self, key, limit, window):
        now = self.clock()
        with self.lock:
            # Expire inactive identities; never evict a live bucket to reset its quota.
            stale = [k for k, (events, seconds) in self.buckets.items() if not events or events[-1] <= now - seconds]
            for k in stale:
                del self.buckets[k]
            if key not in self.buckets:
                if len(self.buckets) >= self.max_keys:
                    raise HTTPException(503, detail={"code": "RATE_LIMIT_UNAVAILABLE"})
                self.buckets[key] = (deque(), window)
            events, _ = self.buckets[key]
            while events and events[0] <= now - window:
                events.popleft()
            if len(events) >= limit:
                return max(1, math.ceil(events[0] + window - now))
            events.append(now)
        return None


class RateLimitMiddleware:
    def __init__(self, app, max_requests_per_minute=120, user_requests_per_minute=120,
                 api_prefix="/api/v1", limiter=None):
        self.app = app
        self.ip_limit = max_requests_per_minute
        self.user_limit = user_requests_per_minute
        self.api_prefix = api_prefix.rstrip("/")
        self.limiter = limiter or SlidingWindowLimiter()

    @staticmethod
    def reject(retry):
        raise HTTPException(429, detail={"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please slow down."},
                            headers={"Retry-After": str(retry)})

    def enforce_user(self, request: Request, actor_id: str):
        # Called by CurrentUser only after the token has been verified.
        path = request.url.path[len(self.api_prefix):].rstrip("/")
        policy = None
        if request.method == "POST":
            if path in ("/ai/privacy/text", "/ai/privacy/image", "/ai/privacy/structured"):
                policy = ("screening", 20, 60)
            elif path.startswith("/groups/") and path.endswith("/invites"):
                policy = ("invites", 10, 3600)
            elif path == "/activities":
                policy = ("activity_creation", 20, 3600)
            elif path.startswith("/activities/") and (path.endswith("/proofs/upload-url") or path.endswith("/proofs/photo")):
                policy = ("proof_upload", 10, 3600)
            elif path.startswith("/activities/") and path.endswith("/proofs"):
                policy = ("proof_submission", 10, 3600)
        policies = [("general", self.user_limit, 60)]
        if policy:
            policies.append(policy)
        for name, limit, seconds in policies:
            retry = self.limiter.check(("user", actor_id, name), limit, seconds)
            if retry:
                self.reject(retry)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope["path"]
        if (scope["method"] == "OPTIONS" or path in ("/health", "/api/health", "/api/openapi.json")
                or not (path == self.api_prefix or path.startswith(self.api_prefix + "/"))):
            return await self.app(scope, receive, send)
        request = Request(scope)
        scope.setdefault("state", {})["rate_limiter"] = self
        # Do not trust raw X-Forwarded-For. Configure trusted proxy IPs in the server.
        ip = request.client.host if request.client else "unknown"
        try:
            retry = self.limiter.check(("ip", ip), self.ip_limit, 60)
            if retry:
                self.reject(retry)
            if path.startswith(self.api_prefix + "/auth/") and request.method == "POST":
                retry = self.limiter.check(("auth_ip", ip), 5, 60)
                if retry:
                    self.reject(retry)
        except HTTPException as exc:
            detail = exc.detail
            code = detail.get("code", "RATE_LIMIT_EXCEEDED")
            message = "Too many requests. Please slow down." if exc.status_code == 429 else "Request limiting is temporarily unavailable."
            return await error_response(scope, exc.status_code, code, message, headers=exc.headers)(scope, receive, send)
        await self.app(scope, receive, send)
