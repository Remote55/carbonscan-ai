"""Logs that can answer "what happened to that one request".

LOG_LEVEL and LOG_FORMAT were settings nothing read, LOG_FORMAT defaulted to
"json" while the service called print(), and structlog was a declared
dependency that was not even installed in the API's own virtualenv. Nothing
here asserts that logging is configured — it asserts what the logs contain,
because that is what makes them worth having.
"""

from __future__ import annotations

import json
import logging

import pytest
import structlog
from fastapi.testclient import TestClient

from app.core.logging import (
    REQUEST_ID_HEADER,
    RequestContextMiddleware,
    configure_logging,
    request_id_var,
)
from app.main import app


@pytest.fixture(autouse=True)
def _restore_logging():
    """Each test reconfigures; put the app's own configuration back after."""
    yield
    configure_logging()


class TestTheRequestId:
    def test_every_response_carries_one(self):
        with TestClient(app) as client:
            response = client.get("/health")
        assert response.headers.get(REQUEST_ID_HEADER), "no request id to quote"

    def test_an_inbound_id_is_kept_so_a_trace_survives_a_proxy(self):
        with TestClient(app) as client:
            response = client.get("/health", headers={REQUEST_ID_HEADER: "abc123"})
        assert response.headers[REQUEST_ID_HEADER] == "abc123"

    def test_two_requests_get_different_ids(self):
        with TestClient(app) as client:
            first = client.get("/health").headers[REQUEST_ID_HEADER]
            second = client.get("/health").headers[REQUEST_ID_HEADER]
        assert first != second

    def test_an_absurdly_long_inbound_id_is_truncated(self):
        """It ends up in every log line and in a response header."""
        with TestClient(app) as client:
            response = client.get("/health", headers={REQUEST_ID_HEADER: "x" * 500})
        assert len(response.headers[REQUEST_ID_HEADER]) <= 64

    def test_the_context_does_not_leak_between_requests(self):
        with TestClient(app) as client:
            client.get("/health")
        assert request_id_var.get() == ""


class TestWhatComesOut:
    def test_json_format_emits_parseable_lines_carrying_the_request_id(
        self, capsys, monkeypatch
    ):
        from app.core import logging as app_logging

        monkeypatch.setattr(app_logging.settings, "LOG_FORMAT", "json")
        monkeypatch.setattr(app_logging.settings, "LOG_LEVEL", "INFO")
        configure_logging()
        token = request_id_var.set("trace-me")
        try:
            structlog.get_logger("test").info("something_happened", tree_count=3)
        finally:
            request_id_var.reset(token)

        line = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()][-1]
        record = json.loads(line)
        assert record["event"] == "something_happened"
        assert record["request_id"] == "trace-me"
        assert record["tree_count"] == 3
        assert record["level"] == "info"
        assert "timestamp" in record

    def test_console_format_is_not_json(self, capsys, monkeypatch):
        from app.core import logging as app_logging

        monkeypatch.setattr(app_logging.settings, "LOG_FORMAT", "console")
        configure_logging()
        structlog.get_logger("test").info("readable_by_a_human")

        line = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()][-1]
        with pytest.raises(json.JSONDecodeError):
            json.loads(line)
        assert "readable_by_a_human" in line

    def test_a_stdlib_logger_comes_out_in_the_same_format(self, capsys, monkeypatch):
        """The codebase uses logging.getLogger(__name__) in several modules, and
        uvicorn logs through stdlib too. Two formats in one stream is one
        format nothing can parse."""
        from app.core import logging as app_logging

        monkeypatch.setattr(app_logging.settings, "LOG_FORMAT", "json")
        configure_logging()
        logging.getLogger("app.somewhere").warning("plain stdlib line")

        line = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()][-1]
        record = json.loads(line)
        assert record["event"] == "plain stdlib line"
        assert record["level"] == "warning"

    def test_log_level_is_honoured(self, capsys, monkeypatch):
        from app.core import logging as app_logging

        monkeypatch.setattr(app_logging.settings, "LOG_FORMAT", "json")
        monkeypatch.setattr(app_logging.settings, "LOG_LEVEL", "WARNING")
        configure_logging()
        structlog.get_logger("test").info("should_not_appear")
        structlog.get_logger("test").warning("should_appear")

        out = capsys.readouterr().out
        assert "should_not_appear" not in out
        assert "should_appear" in out


class TestTheUnhandledExceptionHandler:
    def test_a_crash_returns_a_quotable_id_and_no_internals(self):
        """A bare 500 gives a user nothing to report and may leak a path or a
        query from the exception string."""
        @app.get("/__boom_for_test")
        async def boom():
            raise RuntimeError("secret detail /srv/app/private.key")

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/__boom_for_test")

        assert response.status_code == 500
        body = response.json()
        assert body["error"] == "InternalServerError"
        assert "secret detail" not in json.dumps(body)
        assert "private.key" not in json.dumps(body)
        assert body["request_id"], "nothing to correlate the traceback with"

    def test_the_middleware_ignores_non_http_scopes(self):
        """Lifespan and websocket scopes pass through without a request id."""
        seen: list[dict] = []

        async def downstream(scope, _receive, _send):
            seen.append(scope)

        middleware = RequestContextMiddleware(downstream)

        import asyncio

        asyncio.run(middleware({"type": "lifespan"}, None, None))
        assert seen == [{"type": "lifespan"}]
