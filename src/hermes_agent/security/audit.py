"""Hash-chained, redacted audit records for controller decisions."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .redaction import redact


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


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
        previous_hash = self._last_hash()
        event: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "tool_name": tool_name,
            "arguments_redacted_hash": _digest(redact(arguments)),
            "decision": decision,
            "reason": reason,
            "approval_id": approval_id,
            "result_status": result_status,
            "prev_hash": previous_hash,
        }
        event["event_hash"] = _digest(event)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical(event) + "\n")
        return event

    def verify(self) -> bool:
        if not self.path.exists():
            return True
        previous_hash: str | None = None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
                event_hash = event.pop("event_hash")
            except (TypeError, ValueError, KeyError):
                return False
            if event.get("prev_hash") != previous_hash or _digest(event) != event_hash:
                return False
            previous_hash = event_hash
        return True

    def _last_hash(self) -> str | None:
        if not self.path.exists() or not self.path.stat().st_size:
            return None
        try:
            last_line = self.path.read_text(encoding="utf-8").splitlines()[-1]
            return json.loads(last_line)["event_hash"]
        except (IndexError, KeyError, TypeError, ValueError):
            raise RuntimeError("existing audit log is malformed")
