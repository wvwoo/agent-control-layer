from __future__ import annotations

import json
from pathlib import Path

import pytest

from hermes_agent.tool_protocol import ToolCallError, openai_tools, parse_tool_call


def test_schema_rejects_extra_properties() -> None:
    with pytest.raises(ToolCallError):
        parse_tool_call(
            {
                "name": "workspace_read_text",
                "arguments": {"path": "README.md", "max_bytes": 100, "extra": "no"},
            }
        )


def test_schema_rejects_type_coercion() -> None:
    with pytest.raises(ToolCallError):
        parse_tool_call(
            {
                "name": "workspace_list",
                "arguments": {"path": "", "max_depth": "1", "max_entries": 10},
            }
        )


def test_unknown_tool_never_parses() -> None:
    with pytest.raises(ToolCallError):
        parse_tool_call({"name": "shell", "arguments": {"command": "id"}})


def test_rendered_openai_schemas_are_strict() -> None:
    for tool in openai_tools():
        function = tool["function"]
        assert function["strict"] is True
        assert function["parameters"]["additionalProperties"] is False
        assert set(function["parameters"]["required"]) == set(
            function["parameters"]["properties"]
        )


def test_committed_registry_matches_runtime_schema() -> None:
    registry = json.loads(
        (Path(__file__).resolve().parents[1] / "config" / "tool_registry.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry["tools"] == openai_tools()
