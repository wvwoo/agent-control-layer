"""Controller dispatcher: parse, decide, audit, then perform read-only tools only."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from el_agentctl.policy import PolicyContext, PolicyEngine
from el_agentctl.security.audit import AuditLog
from el_agentctl.tool_protocol import (
    ToolCallError,
    WorkspaceListArguments,
    WorkspaceReadTextArguments,
    parse_tool_call,
)
from el_agentctl.tools.workspace import list_workspace, read_text


class ToolController:
    """A small dispatcher that never lets a model self-authorize execution."""

    def __init__(self, workspace_root: Path, audit_path: Path) -> None:
        self.workspace_root = workspace_root.resolve(strict=True)
        self.audit = AuditLog(audit_path)
        self.policy = PolicyEngine()

    def process(
        self,
        raw_call: str | bytes | dict[str, Any],
        context: PolicyContext | None = None,
    ) -> dict[str, Any]:
        trusted_context = context or PolicyContext()
        try:
            call = parse_tool_call(raw_call)
        except ToolCallError:
            self.audit.append(
                tool_name="invalid",
                arguments={},
                decision="deny",
                reason="invalid tool-call payload",
                result_status="denied",
            )
            return {"status": "denied", "reason": "invalid tool-call payload"}

        decision = self.policy.decide(call, trusted_context)
        arguments = call.arguments.model_dump(mode="json")
        if not decision.allowed:
            self.audit.append(
                tool_name=call.name,
                arguments=arguments,
                decision="deny",
                reason=decision.reason,
                result_status="denied",
            )
            return {
                "status": "denied",
                "reason": decision.reason,
                "requires_human_approval": decision.requires_human_approval,
            }

        result: list[dict[str, str]] | str | dict[str, str | None]
        if isinstance(call.arguments, WorkspaceListArguments):
            result = list_workspace(
                self.workspace_root,
                call.arguments.path,
                call.arguments.max_depth,
                call.arguments.max_entries,
            )
            status = "ok"
        elif isinstance(call.arguments, WorkspaceReadTextArguments):
            result = read_text(
                self.workspace_root,
                call.arguments.path,
                call.arguments.max_bytes,
            )
            status = "ok"
        else:
            # The host application, not this model-facing dispatcher, may hand an
            # approved call to run_approved_python after a separate UI approval.
            result = {"approval_id": trusted_context.approval_id}
            status = "approved_for_sandbox"

        self.audit.append(
            tool_name=call.name,
            arguments=arguments,
            decision="allow",
            reason=decision.reason,
            approval_id=trusted_context.approval_id,
            result_status=status,
        )
        return {"status": status, "result": result}
