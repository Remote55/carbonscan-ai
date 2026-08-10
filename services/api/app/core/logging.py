"""Structured logging, configured once at startup.

LOG_LEVEL and LOG_FORMAT were settings nothing read, and LOG_FORMAT defaulted
to "json" — a claim that the service emitted structured logs when it was
calling print(). structlog was a declared dependency with no importer.

What the service actually needs from logs is the ability to answer "what
happened to that one request", which unlabelled lines interleaved from two
uvicorn workers cannot do. So every record carries a request id, bound by
RequestContextMiddleware and reachable from any logger without threading it
through call signatures.

`json` is the default because a hosted deployment's log viewer parses it.
`console` is for a terminal, where colour and alignment beat machine-readability.
"""

from __future__ import annotations

import logging
import sys
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any

import structlog

from app.core.config import settings

#: The current request's id. A ContextVar rather than a parameter because the
#: alternative is passing it into every function that might log.
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

REQUEST_ID_HEADER = "x-request-id"


def current_request_id(scope: dict[str, Any] | None = None) -> str:
    """This request's id, from the scope if given and the ContextVar otherwise.

    The scope survives where the ContextVar does not: see the note in
    RequestContextMiddleware about ServerErrorMiddleware.
    """
    if scope is not None:
        from_scope = (scope.get("state") or {}).get("request_id")
        if from_scope:
            return str(from_scope)
    return request_id_var.get()


def _add_request_id(_logger: Any, _name: str, event_dict: dict) -> dict:
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging() -> None:
    """Point stdlib logging and structlog at one renderer. Safe to call twice."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _add_request_id,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer: Any = (
        structlog.processors.JSONRenderer()
        if settings.LOG_FORMAT.lower() == "json"
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging through the same processors, so uvicorn's own
    # records and any `logging.getLogger(__name__)` in this codebase come out
    # in one format instead of two.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )
    )
    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True


class RequestContextMiddleware:
    """Give every request an id, and echo it back.

    Reuses an inbound X-Request-Id when there is one so a trace survives a
    proxy hop, and generates one otherwise. The value is echoed in the
    response so a user reporting a failure can quote something findable.
    """

    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        inbound = ""
        for key, value in scope.get("headers", []):
            if key.lower() == REQUEST_ID_HEADER.encode():
                inbound = value.decode("latin-1").strip()[:64]
                break
        request_id = inbound or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        # Also on the scope, because the ContextVar is not enough for the one
        # caller that needs it most. Starlette's ServerErrorMiddleware — where
        # the unhandled-exception handler runs — sits OUTSIDE every middleware
        # added with add_middleware, so an exception has already propagated
        # through the reset below by the time that handler is called, and the
        # ContextVar reads empty exactly when something has gone wrong.
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_id(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((REQUEST_ID_HEADER.encode(), request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            request_id_var.reset(token)
