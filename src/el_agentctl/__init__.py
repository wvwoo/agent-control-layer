"""Exec Logic agent control layer: deny-by-default controller for model tool calls."""

from .tool_protocol import parse_tool_call

__all__ = ["parse_tool_call"]
