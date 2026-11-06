"""Keep rejected preflight responses in the same API error format."""

from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from app.middleware.responses import error_response


class ApiCORSMiddleware(CORSMiddleware):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] == "OPTIONS":
            headers = Headers(scope=scope)
            if "origin" in headers and "access-control-request-method" in headers:
                response = self.preflight_response(headers)
                if response.status_code >= 400:
                    retained = {k: v for k, v in response.headers.items()
                                if k not in ("content-length", "content-type")}
                    response = error_response(scope, 400, "CORS_REJECTED", "Cross-origin request is not allowed.", headers=retained)
                return await response(scope, receive, send)
        await super().__call__(scope, receive, send)
