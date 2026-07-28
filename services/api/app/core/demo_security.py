"""Authentication and rate limiting for the ephemeral judge demo."""

from __future__ import annotations

import hashlib
import hmac
import threading
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi.responses import JSONResponse

from app.core.config import settings

_PROTECTED_PATHS = {
    "/api/v1/upload/analyze",
    "/api/v1/health/demo-ready",
}
_UPLOAD_PATH = "/api/v1/upload/analyze"


def token_matches(expected: str, provided: str) -> bool:
    """Compare non-empty demo tokens without content-dependent comparison."""
    return bool(expected) and bool(provided) and hmac.compare_digest(expected, provided)


def compute_readiness_hmac(token: str, nonce: str) -> str:
    """Bind a caller-provided readiness challenge to the configured demo token."""
    return hmac.new(bytes.fromhex(token), nonce.encode("ascii"), hashlib.sha256).hexdigest()


class DemoGuardMiddleware:
    """Protect only the judge-demo readiness and synchronous upload routes."""

    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app
        self._upload_attempts: dict[str, deque[float]] = defaultdict(deque)
        self._rate_lock = threading.Lock()

    def _allow_upload(self, client: str) -> bool:
        now = time.monotonic()
        cutoff = now - 60
        limit = settings.RATE_LIMIT_UPLOAD
        with self._rate_lock:
            attempts = self._upload_attempts[client]
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if limit <= 0 or len(attempts) >= limit:
                return False
            attempts.append(now)
            return True

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http" or not settings.TREEQ_DEMO_MODE:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path not in _PROTECTED_PATHS:
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        provided = headers.get(b"x-treeq-demo-token", b"").decode("latin-1")
        if not token_matches(settings.TREEQ_DEMO_TOKEN, provided):
            response = JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            await response(scope, receive, send)
            return

        if scope.get("method") == "POST" and path == _UPLOAD_PATH:
            client = (scope.get("client") or ("unknown", 0))[0]
            if not self._allow_upload(str(client)):
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
