from __future__ import annotations

from pathlib import Path

import pytest

from el_agentctl.security.paths import WorkspacePathError, resolve_workspace_path


def test_path_rejects_absolute_traversal_and_sensitive_components(tmp_path: Path) -> None:
    (tmp_path / "public.txt").write_text("safe", encoding="utf-8")
    for requested in [
        "/etc/passwd",
        "../outside",
        ".env",
        ".git/config",
        "secrets/key",
        ".pytest_cache/v",
        "build/output",
        "src/el_agentctl_secure.egg-info/PKG-INFO",
    ]:
        with pytest.raises(WorkspacePathError):
            resolve_workspace_path(tmp_path, requested)


def test_path_rejects_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (tmp_path / "escape").symlink_to(outside)
    with pytest.raises(WorkspacePathError):
        resolve_workspace_path(tmp_path, "escape")


def test_path_resolves_safe_relative_file(tmp_path: Path) -> None:
    safe = tmp_path / "notes.txt"
    safe.write_text("safe", encoding="utf-8")
    assert resolve_workspace_path(tmp_path, "notes.txt") == safe.resolve()
