from __future__ import annotations

from el_agentctl.policy import PolicyContext, PolicyEngine
from el_agentctl.tool_protocol import parse_tool_call


def test_read_only_tool_is_allowed() -> None:
    call = parse_tool_call(
        {
            "name": "workspace_list",
            "arguments": {"path": "", "max_depth": 0, "max_entries": 1},
        }
    )
    assert PolicyEngine().decide(call, PolicyContext()).allowed is True


def test_python_execution_requires_real_approval() -> None:
    call = parse_tool_call({"name": "sandbox_run_python", "arguments": {"code": "print(1)", "timeout_s": 1}})
    denied = PolicyEngine().decide(call, PolicyContext())
    allowed = PolicyEngine().decide(call, PolicyContext(approval_id="operator-001"))
    assert denied.allowed is False
    assert denied.requires_human_approval is True
    assert allowed.allowed is True
