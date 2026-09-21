"""Workspace-only path handling for read-only initial tools."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath


SENSITIVE_COMPONENTS = frozenset(
    {".git", ".env", ".ssh", "secrets", ".hermes", ".venv", "venv"}
)
INTERNAL_COMPONENTS = frozenset({".pytest_cache", "__pycache__", "build", "dist"})


class WorkspacePathError(ValueError):
    """Raised when a path would exceed the approved workspace capability."""


def resolve_workspace_path(workspace_root: Path, requested: str) -> Path:
    """Resolve a safe relative path while rejecting traversal and symlink escape."""

    if not isinstance(requested, str) or "\x00" in requested:
        raise WorkspacePathError("path must be a text value without NUL bytes")

    root = workspace_root.resolve(strict=True)
    raw_path = Path(requested)
    if raw_path.is_absolute() or PureWindowsPath(requested).is_absolute():
        raise WorkspacePathError("absolute paths are not permitted")

    parts = raw_path.parts
    if any(part in {"", ".", ".."} for part in parts):
        if requested not in {"", "."}:
            raise WorkspacePathError("path traversal is not permitted")
    if any(
        part in SENSITIVE_COMPONENTS
        or part in INTERNAL_COMPONENTS
        or part.endswith(".egg-info")
        for part in parts
    ):
        raise WorkspacePathError("path targets a protected workspace component")

    candidate = root.joinpath(*parts)
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise WorkspacePathError("symbolic links are not permitted")

    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise WorkspacePathError("path escapes the approved workspace") from error
    return resolved
