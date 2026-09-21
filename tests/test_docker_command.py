from __future__ import annotations

from pathlib import Path

import pytest

from el_agentctl.executors.docker import build_docker_command


def test_docker_command_is_fixed_and_offline(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    runner = tmp_path / "runner"
    output = tmp_path / "output"
    workspace.mkdir()
    runner.mkdir()
    output.mkdir()
    command = build_docker_command(
        image="el-agentctl-sandbox:dev",
        workspace_root=workspace,
        runner_directory=runner,
        output_directory=output,
    )
    assert command[:4] == ["docker", "run", "--rm", "--init"]
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert command[command.index("--cap-drop") + 1] == "ALL"
    assert command[command.index("--security-opt") + 1] == "no-new-privileges=true"
    assert "--privileged" not in command
    assert "bash" not in command
    assert "-c" not in command


def test_docker_command_rejects_image_injection(tmp_path: Path) -> None:
    for directory in [tmp_path / "workspace", tmp_path / "runner", tmp_path / "output"]:
        directory.mkdir()
    with pytest.raises(ValueError):
        build_docker_command(
            image="agentctl:dev;whoami",
            workspace_root=tmp_path / "workspace",
            runner_directory=tmp_path / "runner",
            output_directory=tmp_path / "output",
        )
