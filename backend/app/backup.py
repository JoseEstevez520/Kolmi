"""Copy the shared Markdown export into an operator-provided private Git checkout."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import subprocess

from .class_settings import read_settings
from .export import build


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True, timeout=120).stdout.strip()


def copy_notebook(client, checkout: str) -> str:
    """Use an existing dedicated checkout with Git credentials already configured by its owner.

    Only `notebook/` is managed. A dirty checkout is refused, and a failed push leaves its commit
    locally for the next run. Raw notes, attachments and credentials never enter the copy.
    """
    if not checkout:
        return "not-configured"
    if not read_settings(client)["export_enabled"]:
        return "disabled"
    repo = Path(checkout).expanduser().resolve()
    if Path(_git(repo, "rev-parse", "--show-toplevel")).resolve() != repo:
        raise ValueError("The backup checkout must be the Git repository root")
    descriptor = os.open(repo / ".kolmi-backup.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Keep the lock outside the worktree status without changing .gitignore.
        status = _git(repo, "status", "--porcelain", "--", ".", ":(exclude).kolmi-backup.lock")
        if status:
            raise ValueError("The backup checkout has uncommitted changes")
        _git(repo, "pull", "--rebase")
        target = repo / "notebook"
        if target.is_symlink():
            raise ValueError("The notebook directory must not be a symlink")
        target.mkdir(exist_ok=True)
        nodes = client.table("nodes").select("id, parent_id, kind, title, description, position, updated_at, content_md").execute().data
        files = build(nodes)
        for old in target.rglob("*.md"):
            if old.is_symlink():
                raise ValueError("The notebook directory must not contain symlinks")
            if old.relative_to(target).as_posix() not in files:
                old.unlink()
        for name, text in files.items():
            path = target / name
            if any(parent.is_symlink() for parent in path.parents if parent != repo.parent):
                raise ValueError("The notebook directory must not contain symlinks")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        _git(repo, "add", "--", "notebook")
        changed = _git(repo, "diff", "--cached", "--name-only")
        if changed:
            _git(repo, "commit", "-m", "docs(notes): update shared notebook")
        # Retry a previous unpushed backup even when the files haven't changed.
        _git(repo, "push")
        return "updated" if changed else "unchanged"
