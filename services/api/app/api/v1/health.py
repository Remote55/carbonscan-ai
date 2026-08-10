"""Health check endpoints — for monitoring + load balancers."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from starlette.concurrency import run_in_threadpool

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


# GET /health/ready was here, answering `SELECT 1` against a database this
# service no longer has. It would have reported "degraded" on a perfectly
# healthy deployment for the absence of something nothing uses — a readiness
# probe pointed at the wrong question. /health/pipeline below is the one that
# matters: it asks whether an analysis can actually run.


#: One successful probe is cached for this long. The probe starts a Python
#: subprocess and imports the pipeline, so an uncached public endpoint would be
#: an invitation. Failures are not cached: a container recovering from a bad
#: mount should report recovered on the next call, not in ten minutes.
_PIPELINE_PROBE_TTL_SECONDS = 600.0
_pipeline_probe: tuple[float, str] | None = None


@router.get("/health/pipeline")
async def pipeline_readiness() -> dict[str, str]:
    """Can this deployment actually run an analysis?

    /health only says uvicorn answered. The image used to ship without the ML
    pipeline at all, so it passed /health while every analysis failed, and the
    only endpoint that checked otherwise - /health/demo-ready - is gated behind
    demo mode, which a public deployment turns off. That left the one question
    worth asking about a new deployment with no way to ask it.

    Unauthenticated on purpose: it reports a version string that already appears
    in the metadata of every analysis, and a readiness probe nobody can reach is
    not a readiness probe.
    """
    global _pipeline_probe

    now = time.monotonic()
    if _pipeline_probe is not None and now - _pipeline_probe[0] < _PIPELINE_PROBE_TTL_SECONDS:
        return {"status": "ok", "pipeline_version": _pipeline_probe[1], "cached": "true"}

    try:
        version = await run_in_threadpool(probe_pipeline_runtime)
    except PipelineError as exc:
        logger.error(
            "pipeline readiness probe failed: %s", redact_operator_detail(exc.operator_detail)
        )
        raise HTTPException(
            status_code=503,
            detail="ML pipeline is not reachable from this deployment",
        ) from exc

    _pipeline_probe = (now, version)
    return {"status": "ok", "pipeline_version": version, "cached": "false"}


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
