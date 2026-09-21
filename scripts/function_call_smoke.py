#!/usr/bin/env python3
"""Exercise the controller with a harmless synthetic function-call payload."""

from __future__ import annotations

import json
from pathlib import Path

from el_agentctl.agent_loop import ToolController

root = Path(__file__).resolve().parents[1]
controller = ToolController(root, root / ".agentctl" / "audit" / "smoke.jsonl")
payload = {
    "name": "workspace_list",
    "arguments": {"path": "", "max_depth": 1, "max_entries": 20},
}
result = controller.process(payload)
print(json.dumps(result, ensure_ascii=False, indent=2))
assert result["status"] == "ok"
assert controller.audit.verify()
