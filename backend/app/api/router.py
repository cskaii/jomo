from fastapi import APIRouter
from app.api.v1.privacy_notice import router as privacy_notice_router
from app.schemas.common import ErrorEnvelope
from app.api.v1 import (
    auth,
    users,
    insights,
    friends,
    groups,
    activities,
    focus,
    locations,
    proofs,
    gardens,
    privacy,
    notifications,
    progression,
)

api_router = APIRouter(responses={
    code: {"model": ErrorEnvelope,
           "description": description}
    for code, description in {
        400: "Invalid request", 401: "Authentication required or invalid token",
        403: "Permission denied", 404: "Resource not found", 409: "Invalid state",
        413: "Request body too large", 415: "Unsupported request encoding",
        422: "Validation failed", 429: "Rate limit exceeded; see Retry-After",
        500: "Unexpected internal error", 501: "Storage integration unavailable",
        503: "Authentication or request limiting unavailable",
    }.items()
})

api_router.include_router(auth.router)
api_router.include_router(privacy_notice_router)
api_router.include_router(users.router)
api_router.include_router(insights.router)
api_router.include_router(friends.router)
api_router.include_router(groups.router)
api_router.include_router(activities.router)
api_router.include_router(focus.router)
api_router.include_router(locations.router)
api_router.include_router(proofs.router)
api_router.include_router(gardens.router)
api_router.include_router(privacy.router)
api_router.include_router(notifications.router)
api_router.include_router(progression.router)
