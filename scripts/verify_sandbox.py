#!/usr/bin/env python3
"""Verify a real approved task cannot establish outbound network access."""

from __future__ import annotations

import os
from pathlib import Path

from el_agentctl.executors.docker import run_approved_python
from el_agentctl.tool_protocol import SandboxRunPythonArguments

root = Path(__file__).resolve().parents[1]
os.environ["AGENTCTL_TEST_SECRET"] = "must-not-enter-sandbox"
task = SandboxRunPythonArguments(
    code=(
        "import os\n"
        "import socket\n"
        "from pathlib import Path\n"
        "if 'AGENTCTL_TEST_SECRET' in os.environ:\n"
        "    raise SystemExit('host secret unexpectedly available')\n"
        "print('SECRET_ABSENT')\n"
        "probe = Path('/workspace/.agentctl-write-probe')\n"
        "try:\n"
        "    probe.write_text('must fail', encoding='utf-8')\n"
        "except OSError:\n"
        "    print('WORKSPACE_READ_ONLY')\n"
        "else:\n"
        "    probe.unlink()\n"
        "    raise SystemExit('workspace unexpectedly writeable')\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=1)\n"
        "except OSError:\n"
        "    print('EGRESS_BLOCKED')\n"
        "else:\n"
        "    raise SystemExit('egress unexpectedly available')\n"
    ),
    timeout_s=5,
)
result = run_approved_python(
    approved_call=task,
    workspace_root=root,
    image="el-agentctl-sandbox:dev",
)
print(result.stdout, end="")
if result.stderr:
    print(result.stderr, end="", file=__import__("sys").stderr)
assert result.exit_code == 0, result
assert "EGRESS_BLOCKED" in result.stdout, result
assert "WORKSPACE_READ_ONLY" in result.stdout, result
assert "SECRET_ABSENT" in result.stdout, result
