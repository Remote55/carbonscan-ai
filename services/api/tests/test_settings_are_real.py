"""Config that names only behaviour the code has.

app/core/config.py already carried a comment explaining why RUNPOD_API_KEY and
RUNPOD_ENDPOINT_ID were deleted — "settings that name an architecture the code
does not have send the next reader looking for a GPU path that was never
built". Nine more settings were doing exactly that in the same file, including
LOG_FORMAT="json", which promised structured logging while the service called
print(), and JWT_SECRET="change-me", a signing key for an auth system nothing
imported.

.env.example is the copy a new developer starts from, so it drifting is the
same defect one step further out.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import Settings

API_ROOT = Path(__file__).resolve().parent.parent
ENV_EXAMPLE = API_ROOT / ".env.example"

#: Settings a deployment sets that no module needs to import. Each one is here
#: because something outside this codebase reads it, not because it is exempt.
CONSUMED_ELSEWHERE = {
    # Pydantic Settings resolves these; they are read as `settings.X` nowhere
    # because they only shape other settings' defaults or the app's identity.
    "APP_NAME",
    "APP_ENV",
    # Read by app/core/logging.py at import time, through the settings object.
    "LOG_LEVEL",
    "LOG_FORMAT",
    # Consumed by pipeline_runner when locating the ML interpreter.
    "ML_DIR",
    "ML_PYTHON",
    # Read via their derived properties rather than directly.
    "CORS_ORIGINS",
    "MAX_UPLOAD_SIZE_MB",
    "TREEQ_DEMO_MAX_UPLOAD_SIZE_MB",
}


def _source_outside_config() -> str:
    """Every application module except the one that declares the settings.

    Searching the whole package including config.py finds each name in its own
    declaration, which is how the first version of this test passed while a
    deliberately-unread setting was added to it.
    """
    config = (API_ROOT / "app/core/config.py").resolve()
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((API_ROOT / "app").rglob("*.py"))
        if path.resolve() != config
    )


def test_every_setting_is_read_by_something():
    source = _source_outside_config()
    unread = sorted(
        name
        for name in Settings.model_fields
        if name not in CONSUMED_ELSEWHERE
        and not re.search(rf"\b{re.escape(name)}\b", source)
    )

    assert not unread, (
        f"declared and never read: {unread}. Either wire them up or delete them "
        "— a setting nobody reads describes behaviour this service does not have. "
        "If a deployment sets it and no module imports it, add it to "
        "CONSUMED_ELSEWHERE with the reason."
    )


def test_env_example_advertises_only_settings_that_exist():
    declared = set(Settings.model_fields)
    advertised = {
        match.group(1)
        for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if (match := re.match(r"^([A-Z][A-Z0-9_]*)=", line.strip()))
    }

    phantom = sorted(advertised - declared)
    assert not phantom, (
        f".env.example lists settings the code does not have: {phantom}. This is "
        "the file a new developer copies."
    )


def test_env_example_does_not_hand_out_a_working_secret():
    """JWT_SECRET shipped with the literal default "change-me" and a sample
    value that looked like an instruction. There is no application secret to
    set any more — auth is Supabase's — and if one returns it must not have a
    usable default."""
    text = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "JWT_SECRET" not in text
    assert "change-me" not in text


def test_the_load_shedding_settings_are_documented_for_an_operator():
    """These two are the whole defence of a public URL, and both have defaults
    that are wrong for a hosted deployment: TRUST_PROXY_HEADERS must be turned
    on behind a proxy, and MAX_CONCURRENT_ANALYSES is sized for a small box."""
    text = ENV_EXAMPLE.read_text(encoding="utf-8")

    for name in ("MAX_CONCURRENT_ANALYSES", "TRUST_PROXY_HEADERS", "RATE_LIMIT_UPLOAD"):
        assert f"{name}=" in text, f"{name} is not in .env.example"
