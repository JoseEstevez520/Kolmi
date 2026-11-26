from pathlib import Path
import subprocess

import pytest

from app import backup


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


class Client:
    def table(self, name):
        assert name == "nodes"
        return self
    def select(self, _):
        return self
    def execute(self):
        return type("R", (), {"data": [{"id": 3, "kind": "page", "title": "Shared", "content_md": "Content"}]})()


def test_backup_copies_only_shared_pages_and_pushes_changed_files(tmp_path, monkeypatch):
    remote = tmp_path / "remote"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    repo = tmp_path / "copy"
    subprocess.run(["git", "clone", str(remote), str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    git(repo, "commit", "--allow-empty", "-m", "Initial")
    git(repo, "push", "-u", "origin", "HEAD")
    monkeypatch.setattr(backup, "read_settings", lambda _: {"export_enabled": True})
    assert backup.copy_notebook(Client(), str(repo)) == "updated"
    assert (repo / "notebook/01-shared.md").exists()
    assert git(repo, "rev-parse", "HEAD") == git(repo, "rev-parse", "@{upstream}")
    assert backup.copy_notebook(Client(), str(repo)) == "unchanged"
    (repo / "notebook/01-shared.md").write_text("local change")
    with pytest.raises(ValueError, match="uncommitted"):
        backup.copy_notebook(Client(), str(repo))


def test_disabled_backup_never_touches_checkout(monkeypatch):
    monkeypatch.setattr(backup, "read_settings", lambda _: {"export_enabled": False})
    assert backup.copy_notebook(Client(), "/nonexistent") == "disabled"
    assert backup.copy_notebook(Client(), "") == "not-configured"
