from contextlib import asynccontextmanager
import asyncio
from contextlib import suppress
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import logger
from app.api.router import api_router
from app.middleware import setup_middleware
from app.db.base import Base
from app.db.session import engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse
import app.models  # ensure all models register with Base.metadata

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing JOMO application...")
    if settings.APP_ENV == "development" and engine.dialect.name == "sqlite":
        from app.db.setup import setup_database
        setup_database(settings.DATABASE_URL, allow_sqlite=True)
    elif settings.APP_ENV == "test" and engine.dialect.name == "sqlite":
        Base.metadata.create_all(bind=engine)
    logger.info("Database engine initialized; readiness is checked at /api/health.")
    if settings.AI_PRESIDIO_ENABLED:
        from starlette.concurrency import run_in_threadpool
        from app.ai.screening_service import get_screening_provider
        await run_in_threadpool(get_screening_provider)
    task = None
    if settings.APP_ENV != "test":
        from app.db.session import SessionLocal
        from app.services.retention_service import cleanup
        from starlette.concurrency import run_in_threadpool
        def run_cleanup():
            with SessionLocal() as db:
                cleanup(db)
        async def retention_worker():
            while True:
                try:
                    await run_in_threadpool(run_cleanup)
                except Exception:
                    logger.error("Retention cleanup failed; retry scheduled. No private values logged.")
                await asyncio.sleep(60)
        task = asyncio.create_task(retention_worker())
    try:
        yield
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
    logger.info("Shutting down JOMO application...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Joy of Missing Out (JOMO) - Less scrolling. More living. Technical implementation foundation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

setup_middleware(
    app,
    cors_origins=settings.cors_origins_list,
    max_requests_per_minute=settings.RATE_LIMIT_IP_PER_MINUTE,
    user_requests_per_minute=settings.RATE_LIMIT_USER_PER_MINUTE,
    max_body_bytes=settings.REQUEST_MAX_BODY_BYTES,
    api_prefix=settings.API_PREFIX,
)

# Include API Router
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["Health"])
async def root_health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/api/health", tags=["Health"])
def api_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "unavailable"})
