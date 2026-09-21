from __future__ import annotations

from pathlib import Path

from hermes_agent.agent_loop import ToolController
from hermes_agent.policy import PolicyContext


def test_controller_lists_workspace_and_audits(tmp_path: Path) -> None:
    (tmp_path / "visible.txt").write_text("hello", encoding="utf-8")
    (tmp_path / ".env").write_text("private", encoding="utf-8")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "generated.txt").write_text("internal", encoding="utf-8")
    (tmp_path / ".pytest_cache").mkdir()
    controller = ToolController(tmp_path, tmp_path / ".hermes" / "audit" / "events.jsonl")

    response = controller.process(
        {
            "name": "workspace_list",
            "arguments": {"path": "", "max_depth": 1, "max_entries": 20},
        }
    )
    assert response["status"] == "ok"
    assert {entry["path"] for entry in response["result"]} == {"visible.txt"}
    assert controller.audit.verify() is True


def test_controller_never_self_approves_python(tmp_path: Path) -> None:
    controller = ToolController(tmp_path, tmp_path / ".hermes" / "audit" / "events.jsonl")
    payload = {
        "name": "sandbox_run_python",
        "arguments": {"code": "print('hello')", "timeout_s": 1},
    }
    denied = controller.process(payload)
    approved = controller.process(payload, PolicyContext(approval_id="real-ui-approval"))
    assert denied["status"] == "denied"
    assert denied["requires_human_approval"] is True
    assert approved["status"] == "approved_for_sandbox"
