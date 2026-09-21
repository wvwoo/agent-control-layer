"""Read-only workspace tools with bounded output."""

from __future__ import annotations

from pathlib import Path

from el_agentctl.security.paths import WorkspacePathError, resolve_workspace_path


class WorkspaceToolError(RuntimeError):
    """Raised for a permitted-but-unavailable workspace resource."""


def list_workspace(
    workspace_root: Path,
    relative_path: str,
    max_depth: int,
    max_entries: int,
) -> list[dict[str, str]]:
    start = resolve_workspace_path(workspace_root, relative_path)
    if not start.exists() or not start.is_dir():
        raise WorkspaceToolError("requested directory does not exist")

    root = workspace_root.resolve(strict=True)
    results: list[dict[str, str]] = []

    def visit(directory: Path, depth: int) -> None:
        if depth > max_depth or len(results) >= max_entries:
            return
        for child in sorted(directory.iterdir(), key=lambda item: item.name):
            if len(results) >= max_entries:
                return
            try:
                safe_child = resolve_workspace_path(root, str(child.relative_to(root)))
            except WorkspacePathError:
                continue
            results.append(
                {
                    "path": str(safe_child.relative_to(root)),
                    "type": "directory" if safe_child.is_dir() else "file",
                }
            )
            if safe_child.is_dir():
                visit(safe_child, depth + 1)

    visit(start, 0)
    return results


def read_text(workspace_root: Path, relative_path: str, max_bytes: int) -> str:
    target = resolve_workspace_path(workspace_root, relative_path)
    if not target.exists() or not target.is_file():
        raise WorkspaceToolError("requested text file does not exist")
    if target.stat().st_size > max_bytes:
        raise WorkspaceToolError("requested text file exceeds the approved byte limit")
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise WorkspaceToolError("requested file is not UTF-8 text") from error
