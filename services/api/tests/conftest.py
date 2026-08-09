"""pytest fixtures."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.demo_security import DemoGuardMiddleware
from app.main import app


@pytest.fixture(autouse=True)
def reset_upload_rate_limiter() -> None:
    """Give each test its own upload budget.

    The limiter counts per client IP in a dict on the middleware instance, and
    that instance lives for the process. Every test shares one address, so they
    used to share one budget of RATE_LIMIT_UPLOAD requests — and a test that
    happened to run after five others got a 429 instead of whatever it was
    checking, depending on collection order.

    This was invisible until the limit stopped being demo-mode-only. Turning it
    on for every mode is the correct behaviour for a public deployment; leaking
    its state between tests never was.
    """
    # Starlette builds the instances lazily, so reach the one actually serving
    # requests by walking the stack rather than the declared middleware list.
    node = getattr(app, "middleware_stack", None)
    while node is not None:
        if isinstance(node, DemoGuardMiddleware):
            node._upload_attempts.clear()
            return
        node = getattr(node, "app", None)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
