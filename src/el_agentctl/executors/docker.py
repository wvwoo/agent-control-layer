"""A fixed offline Docker invocation for approved Python tasks."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from el_agentctl.tool_protocol import SandboxRunPythonArguments

IMAGE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@:-]{0,254}$")


@dataclass(frozen=True)
class DockerExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


def build_docker_command(
    *,
    image: str,
    workspace_root: Path,
    runner_directory: Path,
    output_directory: Path,
) -> list[str]:
    """Build a command without a shell, interpolation, socket, or network."""

    if not IMAGE_PATTERN.fullmatch(image):
        raise ValueError("sandbox image reference contains unsupported characters")

    workspace = workspace_root.resolve(strict=True)
    runner = runner_directory.resolve(strict=True)
    output = output_directory.resolve(strict=True)
    return [
        "docker",
        "run",
        "--rm",
        "--init",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges=true",
        "--user",
        "10001:10001",
        "--pids-limit",
        "128",
        "--memory",
        "512m",
        "--cpus",
        "1",
        "--ulimit",
        "nofile=64:64",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=64m",  # noqa: S108 - tmpfs inside the container, not a host path,
        "--mount",
        f"type=bind,src={workspace},dst=/workspace,readonly",
        "--mount",
        f"type=bind,src={runner},dst=/runner,readonly",
        "--mount",
        f"type=bind,src={output},dst=/output",
        image,
        "python",
        "/runner/task.py",
    ]


def run_approved_python(
    *,
    approved_call: SandboxRunPythonArguments,
    workspace_root: Path,
    image: str,
) -> DockerExecutionResult:
    """Execute only after an external trusted host has supplied an approval."""

    with tempfile.TemporaryDirectory(prefix="agentctl-approved-") as temporary:
        temporary_path = Path(temporary)
        temporary_path.chmod(0o755)
        runner_directory = temporary_path / "runner"
        output_directory = temporary_path / "output"
        runner_directory.mkdir()
        output_directory.mkdir()
        output_directory.chmod(0o777)
        task = runner_directory / "task.py"
        task.write_text(approved_call.code, encoding="utf-8")
        task.chmod(0o644)

        command = build_docker_command(
            image=image,
            workspace_root=workspace_root,
            runner_directory=runner_directory,
            output_directory=output_directory,
        )
        clean_environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        try:
            # Fixed argv built by build_docker_command (no shell, no model-controlled executable).
            process = subprocess.run(  # noqa: S603
                command,
                check=False,
                shell=False,
                env=clean_environment,
                capture_output=True,
                text=True,
                timeout=approved_call.timeout_s + 5,
            )
        except subprocess.TimeoutExpired as error:
            return DockerExecutionResult(
                exit_code=124,
                stdout=_as_text(error.stdout),
                stderr=_as_text(error.stderr) or "sandbox timed out",
                timed_out=True,
            )
        return DockerExecutionResult(process.returncode, process.stdout, process.stderr)


def _as_text(value: bytes | str | None) -> str:
    """TimeoutExpired may carry bytes even when text=True was requested."""
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
