"""Edge cases added in the 2026-09 hardening pass: bounded reads, redaction depth, parser inputs, denials."""

from __future__ import annotations

from pathlib import Path

import pytest

from el_agentctl.agent_loop import ToolController
from el_agentctl.policy import PolicyContext, PolicyEngine
from el_agentctl.security.paths import WorkspacePathError, resolve_workspace_path
from el_agentctl.security.redaction import redact
from el_agentctl.tool_protocol import ParsedToolCall, ToolCallError, WorkspaceListArguments, parse_tool_call
from el_agentctl.tools.workspace import WorkspaceToolError, list_workspace, read_text


def _tree(root: Path) -> None:
    (root / "a" / "b" / "c").mkdir(parents=True)
    (root / "a" / "one.txt").write_text("1", encoding="utf-8")
    (root / "a" / "b" / "two.txt").write_text("2", encoding="utf-8")
    (root / "a" / "b" / "c" / "three.txt").write_text("3", encoding="utf-8")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("secret", encoding="utf-8")


def test_list_respects_depth_and_entry_limits(tmp_path: Path) -> None:
    _tree(tmp_path)
    shallow = {e["path"] for e in list_workspace(tmp_path, "a", max_depth=0, max_entries=50)}
    assert shallow == {"a/b", "a/one.txt"}
    capped = list_workspace(tmp_path, "", max_depth=5, max_entries=2)
    assert len(capped) == 2
    everything = {e["path"] for e in list_workspace(tmp_path, "", max_depth=5, max_entries=50)}
    assert not any(p.startswith(".git") for p in everything)


def test_list_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceToolError):
        list_workspace(tmp_path, "missing", max_depth=1, max_entries=5)


def test_read_text_limits(tmp_path: Path) -> None:
    (tmp_path / "big.txt").write_text("x" * 100, encoding="utf-8")
    (tmp_path / "bin.dat").write_bytes(b"\xff\xfe\x00\x80")
    assert read_text(tmp_path, "big.txt", max_bytes=100) == "x" * 100
    with pytest.raises(WorkspaceToolError, match="byte limit"):
        read_text(tmp_path, "big.txt", max_bytes=99)
    with pytest.raises(WorkspaceToolError, match="UTF-8"):
        read_text(tmp_path, "bin.dat", max_bytes=100)
    with pytest.raises(WorkspaceToolError, match="does not exist"):
        read_text(tmp_path, "nope.txt", max_bytes=100)


def test_path_rejects_nul_and_non_text(tmp_path: Path) -> None:
    with pytest.raises(WorkspacePathError):
        resolve_workspace_path(tmp_path, "a\x00b")
    with pytest.raises(WorkspacePathError):
        resolve_workspace_path(tmp_path, 42)  # type: ignore[arg-type]


def test_redaction_reaches_nested_lists_and_tuples() -> None:
    value = {"items": [{"api_key": "k"}, ({"Authorization": "b"},)], "safe": ("x", 1)}
    assert redact(value) == {
        "items": [{"api_key": "[REDACTED]"}, [{"Authorization": "[REDACTED]"}]],
        "safe": ["x", 1],
    }


@pytest.mark.parametrize("raw", ["{not json", b"\xff", 42, None])
def test_parser_rejects_bad_payloads(raw: object) -> None:
    with pytest.raises(ToolCallError):
        parse_tool_call(raw)  # type: ignore[arg-type]


def test_parser_accepts_bytes_json() -> None:
    call = parse_tool_call(b'{"name":"workspace_list","arguments":{"path":"","max_depth":1,"max_entries":5}}')
    assert call.name == "workspace_list"


def test_invalid_payload_is_denied_and_audited(tmp_path: Path) -> None:
    controller = ToolController(tmp_path, tmp_path / ".agentctl" / "audit" / "events.jsonl")
    response = controller.process("{broken")
    assert response == {"status": "denied", "reason": "invalid tool-call payload"}
    assert controller.audit.verify()
    assert "invalid" in (tmp_path / ".agentctl" / "audit" / "events.jsonl").read_text(encoding="utf-8")


def test_read_text_through_controller(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")
    controller = ToolController(tmp_path, tmp_path / ".agentctl" / "audit" / "events.jsonl")
    response = controller.process(
        {"name": "workspace_read_text", "arguments": {"path": "note.txt", "max_bytes": 100}}
    )
    assert response == {"status": "ok", "result": "hello"}


def test_unknown_tool_name_is_denied_by_policy() -> None:
    call = ParsedToolCall(
        name="free_form_shell", arguments=WorkspaceListArguments(path="", max_depth=1, max_entries=1)
    )  # type: ignore[arg-type]
    decision = PolicyEngine().decide(call, PolicyContext())
    assert decision.allowed is False
    assert "not enabled" in decision.reason
