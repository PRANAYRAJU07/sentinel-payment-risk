"""
Sentinel Backend — Health Check API Router
"""
import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("health")

_start_time = time.time()


@router.get("/health", tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    System health check.
    Returns status of backend, database, and model.
    """
    settings = get_settings()
    uptime_seconds = round(time.time() - _start_time)

    # Check database
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        db_status = "unhealthy"

    # Check model (will be updated in Phase 7)
    model_status = "not_loaded"
    try:
        from app.risk.risk_engine import get_risk_engine
        engine = get_risk_engine()
        if engine.is_ready():
            model_status = "loaded"
        else:
            model_status = "not_loaded"
    except Exception:
        model_status = "not_loaded"

    overall = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall,
        "version": settings.app_version,
        "environment": settings.app_env,
        "demo_mode": settings.demo_mode,
        "uptime_seconds": uptime_seconds,
        "components": {
            "database": db_status,
            "model": model_status,
            "razorpay": "configured" if settings.has_razorpay else "not_configured",
            "llm": "configured" if settings.has_llm else "not_configured",
        },
        "mode": "TEST/DEMO — Not a production payment system",
    }
