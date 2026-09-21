from __future__ import annotations

from pathlib import Path

from hermes_agent.security.audit import AuditLog


def test_audit_chain_verifies_and_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    audit = AuditLog(path)
    audit.append(
        tool_name="workspace_list",
        arguments={"path": "", "api_key": "must-not-appear"},
        decision="allow",
        reason="test",
    )
    audit.append(
        tool_name="sandbox_run_python",
        arguments={"code": "print(1)"},
        decision="deny",
        reason="approval required",
    )
    assert audit.verify() is True
    assert "must-not-appear" not in path.read_text(encoding="utf-8")

    path.write_text(path.read_text(encoding="utf-8").replace("allow", "tampered", 1), encoding="utf-8")
    assert audit.verify() is False
