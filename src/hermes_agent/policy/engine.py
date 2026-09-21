"""Deterministic policy decisions independent of model text."""

from __future__ import annotations

from dataclasses import dataclass

from hermes_agent.tool_protocol import ParsedToolCall


@dataclass(frozen=True)
class PolicyContext:
    """Trusted context supplied by the host application, never by the model."""

    approval_id: str | None = None


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    requires_human_approval: bool = False


class PolicyEngine:
    """Initial policy: read-only files are allowed; execution needs real approval."""

    READ_ONLY_TOOLS = frozenset({"workspace_list", "workspace_read_text"})

    def decide(self, call: ParsedToolCall, context: PolicyContext) -> PolicyDecision:
        if call.name in self.READ_ONLY_TOOLS:
            return PolicyDecision(True, "read-only workspace capability")

        if call.name == "sandbox_run_python":
            if context.approval_id and context.approval_id.strip():
                return PolicyDecision(True, "trusted human approval attached")
            return PolicyDecision(
                False,
                "sandbox execution requires trusted human approval",
                requires_human_approval=True,
            )

        return PolicyDecision(False, "tool is not enabled by policy")
