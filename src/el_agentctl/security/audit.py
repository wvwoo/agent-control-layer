"""Hash-chained, redacted audit records for controller decisions.

Concurrency: every append takes an exclusive advisory lock (flock) on the log file, reads the
last event hash and writes the new event while holding the lock, then fsyncs. Several processes
or workers can therefore share one log without forking the chain.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any

from .redaction import redact

_TAIL_CHUNK = 4096


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _last_line(handle: IO[bytes]) -> bytes | None:
    """Return the last non-empty line of a binary file without reading the whole file."""
    handle.seek(0, os.SEEK_END)
    end = handle.tell()
    if end == 0:
        return None
    buffer = b""
    position = end
    while position > 0:
        step = min(_TAIL_CHUNK, position)
        position -= step
        handle.seek(position)
        buffer = handle.read(step) + buffer
        stripped = buffer.rstrip(b"\n")
        if b"\n" in stripped:
            return stripped.rsplit(b"\n", 1)[1]
    return buffer.rstrip(b"\n") or None


class AuditLogError(RuntimeError):
    """The audit log exists but cannot be trusted."""


class AuditLog:
    """Local integrity evidence, not a substitute for protected remote signing."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        decision: str,
        reason: str,
        approval_id: str | None = None,
        result_status: str | None = None,
    ) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                event: dict[str, Any] = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "tool_name": tool_name,
                    "arguments_redacted_hash": _digest(redact(arguments)),
                    "decision": decision,
                    "reason": reason,
                    "approval_id": approval_id,
                    "result_status": result_status,
                    "prev_hash": self._last_hash(handle),
                }
                event["event_hash"] = _digest(event)
                handle.write((_canonical(event) + "\n").encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return event

    def verify(self) -> bool:
        if not self.path.exists():
            return True
        previous_hash: str | None = None
        with self.path.open("rb") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                lines = handle.read().decode("utf-8").splitlines()
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        for line in lines:
            try:
                event = json.loads(line)
                event_hash = event.pop("event_hash")
            except (TypeError, ValueError, KeyError):
                return False
            if event.get("prev_hash") != previous_hash or _digest(event) != event_hash:
                return False
            previous_hash = event_hash
        return True

    @staticmethod
    def _last_hash(handle: IO[bytes]) -> str | None:
        line = _last_line(handle)
        if line is None:
            return None
        try:
            value = json.loads(line.decode("utf-8"))["event_hash"]
        except (KeyError, TypeError, ValueError, UnicodeDecodeError):
            raise AuditLogError("existing audit log is malformed") from None
        if not isinstance(value, str) or len(value) != 64:
            raise AuditLogError("existing audit log has an invalid event hash")
        return value
