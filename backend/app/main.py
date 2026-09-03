"""
Sentinel Backend — Main FastAPI Application
⚠️  DEMO / TEST MODE — Not a production payment system ⚠️
"""
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.database import get_db_engine, Base
import app.models  # noqa: F401 — registers all models with SQLAlchemy metadata
from app.core.errors import (
    validation_exception_handler,
    generic_exception_handler,
    sentinel_exception_handler,
    SentinelException,
)
from app.api.health import router as health_router
from app.api.endpoints.risk import router as risk_router
from app.api.endpoints.behavior import router as behavior_router

# Configure logging before anything else
configure_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown."""
    settings = get_settings()
    logger.info(
        "sentinel_starting",
        version=settings.app_version,
        environment=settings.app_env,
        demo_mode=settings.demo_mode,
        note="TEST/DEMO MODE — Not a production payment system",
    )

    # Create database tables
    engine = get_db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")

    yield  # Application runs here

    # Shutdown
    await engine.dispose()
    logger.info("sentinel_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Sentinel — AI-Powered Payment Risk Control Tower",
        description=(
            "⚠️ **DEMO / TEST MODE** — This is a portfolio demonstration project. "
            "It uses Razorpay TEST MODE only. No real money is processed.\n\n"
            "Sentinel combines real-time risk scoring, behavioral anomaly detection, "
            "fraud-network graph analysis, and AI-powered investigation reports."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # -----------------------------------------------
    # CORS — allow frontend origin only
    # -----------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # -----------------------------------------------
    # Request ID middleware
    # -----------------------------------------------
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        response = await call_next(request)

        process_time = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(process_time)

        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            process_time_ms=process_time,
        )
        return response

    # -----------------------------------------------
    # Exception Handlers
    # -----------------------------------------------
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SentinelException, sentinel_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # -----------------------------------------------
    # Routers
    # -----------------------------------------------
    api_prefix = "/api/v1"
    app.include_router(health_router, prefix=api_prefix)
    app.include_router(risk_router, prefix=api_prefix + "/risk", tags=["risk"])
    app.include_router(behavior_router, prefix=api_prefix + "/behavior", tags=["behavior"])

    # Routers will be added incrementally in later phases:
    # app.include_router(transactions_router, prefix=api_prefix)
    # app.include_router(risk_router, prefix=api_prefix)
    # app.include_router(webhooks_router, prefix=api_prefix)
    # app.include_router(fraud_clusters_router, prefix=api_prefix)
    # app.include_router(investigations_router, prefix=api_prefix)
    # app.include_router(simulator_router, prefix=api_prefix)
    # app.include_router(models_router, prefix=api_prefix)
    # app.include_router(audit_router, prefix=api_prefix)
    # app.include_router(analyst_router, prefix=api_prefix)
    # app.include_router(metrics_router, prefix=api_prefix)

    return app


app = create_app()
