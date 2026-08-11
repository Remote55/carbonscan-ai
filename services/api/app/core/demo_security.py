"""Authentication and rate limiting for the ephemeral judge demo."""

from __future__ import annotations

import hashlib
import hmac
import threading
import time
from collections import OrderedDict, deque

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings

_PROTECTED_PATHS = {
    "/api/v1/upload/analyze",
    "/api/v1/health/demo-ready",
}
# Paths whose last segment is an id, so they cannot be matched exactly. The
# segmented-cloud download carries the same data the analysis did and must sit
# behind the same token; without this an id would be a public download link.
_PROTECTED_PREFIXES = ("/api/v1/upload/segmented/",)
_UPLOAD_PATH = "/api/v1/upload/analyze"


def is_protected_path(path: str) -> bool:
    """Whether the demo token is required for this request path."""
    return path in _PROTECTED_PATHS or path.startswith(_PROTECTED_PREFIXES)


def _is_strong_hex_token(token: str) -> bool:
    if len(token) < 64 or len(token) % 2:
        return False
    try:
        decoded = bytes.fromhex(token)
    except ValueError:
        return False
    return len(decoded) >= 32 and len(token) == len(decoded) * 2


def token_matches(expected: str, provided: str) -> bool:
    """Compare demo tokens only when both contain at least 256 bits of hex.

    Both operands are shape-checked before the comparison, not after. The
    header arrives decoded as latin-1, so any byte above 0x7f produces a str
    that CPython's compare_digest refuses outright:

        TypeError: comparing strings with non-ASCII characters is not supported

    Written as `compare_digest(...) and _is_strong_hex_token(provided)`, the
    comparison ran first and that TypeError escaped as an unhandled 500 from
    the pre-auth path — reachable by anyone, one traceback per request. It
    failed closed, but a crash is not a decision.

    Checking the shape first leaks only whether the caller sent well-formed
    hex, which is not the secret; compare_digest still guards the value.
    """
    if not _is_strong_hex_token(expected) or not _is_strong_hex_token(provided):
        return False
    return hmac.compare_digest(expected, provided)


def compute_readiness_hmac(token: str, nonce: str) -> str:
    """Bind a caller-provided readiness challenge to the configured demo token."""
    return hmac.new(bytes.fromhex(token), nonce.encode("ascii"), hashlib.sha256).hexdigest()


def client_key(scope: Scope) -> str:
    """The address to rate-limit by.

    ``scope["client"]`` is the socket peer. Behind Railway, Fly, HF Spaces or
    Cloudflare that is the proxy, not the caller, so keying on it puts every
    user of a deployed service into ONE bucket — RATE_LIMIT_UPLOAD for the whole
    world, where the first caller starves the rest.

    X-Forwarded-For fixes that and is caller-controlled, so it is only read when
    the operator states that a proxy is in front. Otherwise anyone could send a
    fresh value per request and have no limit at all. The left-most entry is the
    original client; a proxy appends, so entries to its right are hops.
    """
    peer = str((scope.get("client") or ("unknown", 0))[0])
    if not settings.TRUST_PROXY_HEADERS:
        return peer
    for key, value in scope.get("headers", []):
        if key.lower() == b"x-forwarded-for":
            first: str = value.decode("latin-1").split(",")[0].strip()
            if first:
                return first
    return peer


class DemoGuardMiddleware:
    """Protect only the judge-demo readiness and synchronous upload routes."""

    #: Distinct clients tracked at once. Without a bound the table grows by one
    #: entry per address seen and never shrinks — a slow leak on a public URL,
    #: since a client's entry was only pruned when that same client returned.
    #:
    #: Expiry alone cannot bound it: a burst of addresses that are all recent
    #: leaves nothing to expire, so the table has to evict as well. Eviction is
    #: least-recently-seen, which means flushing a victim's budget takes
    #: MAX_TRACKED_CLIENTS distinct addresses inside the 60 s window rather than
    #: a couple. That trade is inherent to bounding the table at all, and an
    #: unbounded one is the worse answer.
    MAX_TRACKED_CLIENTS = 4096

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._upload_attempts: OrderedDict[str, deque[float]] = OrderedDict()
        self._rate_lock = threading.Lock()

    def _allow_upload(self, client: str) -> bool:
        now = time.monotonic()
        cutoff = now - 60
        limit = settings.RATE_LIMIT_UPLOAD
        with self._rate_lock:
            attempts = self._upload_attempts.get(client)
            if attempts is None:
                attempts = deque()
                self._upload_attempts[client] = attempts
                if len(self._upload_attempts) > self.MAX_TRACKED_CLIENTS:
                    # Cheap first: drop whatever has aged out. Only if that
                    # frees nothing does anyone lose a live budget.
                    for key in [
                        key
                        for key, seen in self._upload_attempts.items()
                        if key != client and (not seen or seen[-1] <= cutoff)
                    ]:
                        del self._upload_attempts[key]
                while len(self._upload_attempts) > self.MAX_TRACKED_CLIENTS:
                    self._upload_attempts.popitem(last=False)
            self._upload_attempts.move_to_end(client)

            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if limit <= 0 or len(attempts) >= limit:
                return False
            attempts.append(now)
            return True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not is_protected_path(path):
            await self.app(scope, receive, send)
            return

        # The token gates WHO may call this. It is only meaningful in demo mode,
        # where a URL is handed out deliberately.
        if settings.TREEQ_DEMO_MODE:
            headers = {key.lower(): value for key, value in scope.get("headers", [])}
            provided = headers.get(b"x-treeq-demo-token", b"").decode("latin-1")
            if not token_matches(settings.TREEQ_DEMO_TOKEN, provided):
                response = JSONResponse(status_code=401, content={"detail": "Unauthorized"})
                await response(scope, receive, send)
                return

        # The rate limit is a different question - how much work one caller may
        # ask for - and the answer does not depend on whether a token was
        # checked. This used to sit inside the demo-mode branch, so turning demo
        # mode off removed the limit along with the token, on the one route that
        # runs a multi-minute subprocess. Analysis is unauthenticated either way,
        # so with the limit gone a single anonymous caller could hold the
        # instance indefinitely.
        if scope.get("method") == "POST" and path == _UPLOAD_PATH:
            if not self._allow_upload(client_key(scope)):
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
