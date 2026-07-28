"""Health check endpoints — for monitoring + load balancers."""

import logging
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.api.deps import DbSession
from app.core.config import settings
from app.core.demo_security import compute_readiness_hmac
from app.services.pipeline_runner import (
    PipelineError,
    probe_pipeline_runtime,
    redact_operator_detail,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — returns immediately."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(db: DbSession) -> dict[str, str | bool]:
    """Readiness probe — checks DB connection."""
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
    }


@router.get("/health/demo-ready")
async def demo_readiness(
    challenge: Annotated[str, Header(alias="X-TreeQ-Demo-Challenge")],
) -> dict[str, str]:
    """Prove that the authenticated demo caller reached a usable ML runtime."""
    if not settings.TREEQ_DEMO_MODE:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        pipeline_version = await run_in_threadpool(probe_pipeline_runtime, timeout=30)
        challenge_hmac = compute_readiness_hmac(settings.TREEQ_DEMO_TOKEN, challenge)
    except PipelineError as exc:
        logger.error("Pipeline readiness failed: %s", redact_operator_detail(exc.operator_detail))
        raise HTTPException(status_code=503, detail="Pipeline runtime unavailable") from exc
    except (UnicodeEncodeError, ValueError) as exc:
        logger.error("Invalid demo readiness configuration")
        raise HTTPException(status_code=503, detail="Demo readiness unavailable") from exc
    return {
        "status": "ready",
        "mode": "demo",
        "pipeline_version": pipeline_version,
        "challenge_hmac": challenge_hmac,
    }
