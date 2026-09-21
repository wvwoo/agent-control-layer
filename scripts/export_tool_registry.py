#!/usr/bin/env python3
"""Print the live strict tool registry for a chosen serving adapter."""

from __future__ import annotations

import json

from hermes_agent.tool_protocol import openai_tools


print(
    json.dumps(
        {
            "version": 1,
            "note": (
                "Generated semantics: all properties are required for strict tool-calling "
                "compatibility. The runtime independently validates every call."
            ),
            "tools": openai_tools(),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)
