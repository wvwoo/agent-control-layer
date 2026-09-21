"""Strict, model-agnostic parsing for the tiny initial tool registry."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, ValidationError


ToolName: TypeAlias = Literal[
    "workspace_list",
    "workspace_read_text",
    "sandbox_run_python",
]


class ToolCallError(ValueError):
    """Raised when an untrusted tool-call payload fails strict validation."""


class StrictToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class WorkspaceListArguments(StrictToolArguments):
    path: str = Field(max_length=512)
    max_depth: int = Field(ge=0, le=3)
    max_entries: int = Field(ge=1, le=200)


class WorkspaceReadTextArguments(StrictToolArguments):
    path: str = Field(min_length=1, max_length=512)
    max_bytes: int = Field(ge=1, le=65_536)


class SandboxRunPythonArguments(StrictToolArguments):
    code: str = Field(min_length=1, max_length=16_384)
    timeout_s: int = Field(ge=1, le=30)


ToolArguments: TypeAlias = (
    WorkspaceListArguments | WorkspaceReadTextArguments | SandboxRunPythonArguments
)


class ToolEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: ToolName
    arguments: dict[str, Any]


ARGUMENT_MODELS: dict[str, type[StrictToolArguments]] = {
    "workspace_list": WorkspaceListArguments,
    "workspace_read_text": WorkspaceReadTextArguments,
    "sandbox_run_python": SandboxRunPythonArguments,
}


@dataclass(frozen=True)
class ParsedToolCall:
    name: ToolName
    arguments: ToolArguments


def parse_tool_call(raw: str | bytes | Mapping[str, Any]) -> ParsedToolCall:
    """Parse one untrusted tool call without coercing types or accepting extras."""

    if isinstance(raw, (str, bytes)):
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError) as error:
            raise ToolCallError("tool call must be valid JSON") from error
    elif isinstance(raw, Mapping):
        payload = dict(raw)
    else:
        raise ToolCallError("tool call must be a JSON object")

    try:
        envelope = ToolEnvelope.model_validate(payload, strict=True)
        arguments = ARGUMENT_MODELS[envelope.name].model_validate(
            envelope.arguments,
            strict=True,
        )
    except ValidationError as error:
        raise ToolCallError("tool call violates the registered schema") from error

    return ParsedToolCall(name=envelope.name, arguments=arguments)


def _strict_parameters(model: type[StrictToolArguments]) -> dict[str, Any]:
    """Render OpenAI-compatible parameters without making runtime policy implicit."""

    schema = model.model_json_schema()
    schema.pop("title", None)
    schema["additionalProperties"] = False
    schema["required"] = list(schema["properties"])
    for property_schema in schema["properties"].values():
        property_schema.pop("title", None)
    for definition in schema.get("$defs", {}).values():
        definition["additionalProperties"] = False
    return schema


def openai_tools() -> list[dict[str, Any]]:
    """Return strict schemas; parser output still requires controller authorization."""

    descriptions = {
        "workspace_list": "List non-sensitive entries below the approved workspace root.",
        "workspace_read_text": "Read bounded UTF-8 text below the approved workspace root.",
        "sandbox_run_python": (
            "Run bounded Python only after a real human approval has been attached "
            "by the trusted controller."
        ),
    }
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": descriptions[name],
                "strict": True,
                "parameters": _strict_parameters(model),
            },
        }
        for name, model in ARGUMENT_MODELS.items()
    ]
