"""Small, deterministic redaction helpers for audit metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SENSITIVE_KEY_MARKERS = ("secret", "token", "password", "api_key", "apikey", "authorization")


def redact(value: Any) -> Any:
    """Redact values by key name before they enter local audit records."""

    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]"
            if any(marker in str(key).lower() for marker in SENSITIVE_KEY_MARKERS)
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    return value
