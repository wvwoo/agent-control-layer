from __future__ import annotations

from pathlib import Path

from el_agentctl.security.audit import AuditLog


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


def _append_many(path: str, worker: int, count: int) -> None:
    from pathlib import Path as _Path

    from el_agentctl.security.audit import AuditLog as _AuditLog

    log = _AuditLog(_Path(path))
    for index in range(count):
        log.append(
            tool_name="workspace_list", arguments={"i": index, "w": worker}, decision="allow", reason="test"
        )


def test_concurrent_writers_keep_one_unbroken_chain(tmp_path):
    import multiprocessing

    from el_agentctl.security.audit import AuditLog as _AuditLog

    path = tmp_path / "audit" / "events.jsonl"
    context = multiprocessing.get_context("spawn")
    workers = [context.Process(target=_append_many, args=(str(path), w, 25)) for w in range(4)]
    for process in workers:
        process.start()
    for process in workers:
        process.join(timeout=60)
        assert process.exitcode == 0
    assert len(path.read_text(encoding="utf-8").splitlines()) == 100
    assert _AuditLog(path).verify()


def test_malformed_last_line_is_refused(tmp_path):
    import pytest

    from el_agentctl.security.audit import AuditLog as _AuditLog
    from el_agentctl.security.audit import AuditLogError

    path = tmp_path / "events.jsonl"
    path.write_text("not json\n", encoding="utf-8")
    with pytest.raises(AuditLogError):
        _AuditLog(path).append(tool_name="t", arguments={}, decision="deny", reason="r")


def test_last_line_is_read_from_the_tail_of_a_large_log(tmp_path):
    from el_agentctl.security.audit import AuditLog as _AuditLog

    path = tmp_path / "events.jsonl"
    log = _AuditLog(path)
    for index in range(300):
        log.append(tool_name="workspace_list", arguments={"i": index}, decision="allow", reason="x" * 50)
    assert log.verify()
