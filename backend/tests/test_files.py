from __future__ import annotations

import io
import zipfile
from typing import Any

import pytest
from fastapi import HTTPException
from postgrest.exceptions import APIError

from app.actions.files import FileIdParams, NoteFilesParams, delete_file, download_file, note_files
from app.agents.gatekeeper import _notes, build_index, run_gatekeeper
from app.auth import Context
from app.files import MAX_FILE_BYTES, MAX_FILES_PER_NOTE, check_file, node_files, peek
from app.files_api import store_upload
from app.passes.daily import run_daily_pass
from tests.fakes import FakeLLM, FakeStore


class _Query:
    def __init__(self, table, op, data=None):
        self.table, self.op, self.data, self.filters = table, op, data, []

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, *_a, **_k):
        return self

    def limit(self, _n):
        return self

    def execute(self):
        if self.table.missing:
            raise APIError({"code": "PGRST205", "message": "Could not find the table in the schema cache"})
        rows = [r for r in self.table.rows if all(r.get(c) == v for c, v in self.filters)]
        if self.op == "insert":
            stored = {"id": len(self.table.rows) + 1, **self.data}
            self.table.rows.append(stored)
            rows = [stored]
        elif self.op == "delete":
            self.table.rows[:] = [r for r in self.table.rows if r not in rows]
        return type("Response", (), {"data": [dict(r) for r in rows]})()


class _Table:
    def __init__(self, rows=(), missing=False):
        self.rows, self.missing = list(rows), missing

    def select(self, _c):
        return _Query(self, "select")

    def insert(self, row):
        return _Query(self, "insert", row)

    def delete(self):
        return _Query(self, "delete")


class _Bucket:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def upload(self, path, data, options=None):
        self.objects[path] = data

    def remove(self, paths):
        for path in paths:
            self.objects.pop(path, None)

    def create_signed_url(self, path, seconds, options=None):
        return {"signedURL": f"https://storage/{path}?token=t&download={options['download']}"}


class _Client:
    def __init__(self, missing=False):
        self.notes = _Table([
            {"id": 1, "user_id": "u1", "status": "pending"},
            {"id": 2, "user_id": "u1", "status": "processed"},
        ])
        self.nodes = _Table([{"id": 20}])
        self.files = _Table(missing=missing)
        self.bucket = _Bucket()
        self.storage = type("Storage", (), {"from_": lambda _s, _n: self.bucket})()

    def table(self, name):
        return getattr(self, name)


def ctx(client, user="u1", role="student", approved=True):
    return Context(user_id=user, email=None, profile={"approved": approved, "role": role}, client=client)


def put(client, who=None, **kw):
    kw = {"name": "notes.pdf", "mime": "application/pdf", "data": b"%PDF-1.4 hi", "note_id": 1, **kw}
    return store_upload(who or ctx(client), **kw)


# --- limits and kinds ---


@pytest.mark.parametrize("name,mime", [
    ("a.zip", "application/zip"), ("a.pdf", "application/pdf"), ("main.py", ""),
    ("n.md", "text/markdown"), ("x.json", "application/json"),
    ("t.csv", "application/vnd.ms-excel"), ("p.PNG", "image/png"), ("c.yaml", "application/octet-stream"),
])
def test_the_allowed_kinds_pass(name, mime):
    check_file(name, mime, 10)


@pytest.mark.parametrize("name,mime", [
    ("setup.exe", "application/x-msdownload"), ("run.sh", "text/x-shellscript"),
    ("a.bat", "text/plain"), ("noext", "text/plain"), ("x.svg", "image/svg+xml"),
    ("a.pdf", "image/png"), ("a.zip", "text/html"), ("main.ts", "video/mp2t"),
])
def test_executables_and_unknown_kinds_are_refused(name, mime):
    with pytest.raises(HTTPException) as error:
        check_file(name, mime, 10)
    assert error.value.status_code == 415


def test_size_limits():
    with pytest.raises(HTTPException) as error:
        check_file("a.txt", "text/plain", MAX_FILE_BYTES + 1)
    assert error.value.status_code == 413
    with pytest.raises(HTTPException):
        check_file("a.txt", "text/plain", 0)
    check_file("a.txt", "text/plain", MAX_FILE_BYTES)


def test_the_bytes_must_match_the_kind():
    with pytest.raises(HTTPException):
        check_file("a.pdf", "application/pdf", 5, b"hello")
    with pytest.raises(HTTPException):
        check_file("a.zip", "application/zip", 5, b"hello")


def test_a_note_carries_a_few_files():
    client = _Client()
    for _ in range(MAX_FILES_PER_NOTE):
        put(client)
    with pytest.raises(HTTPException) as error:
        put(client)
    assert error.value.status_code == 409


# --- who may upload, download, delete ---


def test_an_author_attaches_to_their_pending_note():
    client = _Client()
    row = put(client)
    assert row["note_id"] == 1 and row["node_id"] is None and "path" not in row
    assert len(client.bucket.objects) == 1
    assert client.files.rows[0]["user_id"] == "u1"


def test_not_someone_elses_note_nor_a_closed_one():
    client = _Client()
    with pytest.raises(HTTPException) as error:
        put(client, ctx(client, "u2"))
    assert error.value.status_code == 404
    with pytest.raises(HTTPException) as error:
        put(client, note_id=2)
    assert error.value.status_code == 409
    assert not client.bucket.objects


def test_only_an_admin_attaches_to_a_page():
    client = _Client()
    with pytest.raises(HTTPException) as error:
        put(client, node_id=20, note_id=None)
    assert error.value.status_code == 403
    row = put(client, ctx(client, "a1", "admin"), node_id=20, note_id=None)
    assert row["node_id"] == 20 and row["note_id"] is None
    with pytest.raises(HTTPException) as error:
        put(client, ctx(client, "a1", "admin"), node_id=99, note_id=None)
    assert error.value.status_code == 404


def test_a_profile_that_is_not_approved_is_refused():
    client = _Client()
    with pytest.raises(HTTPException) as error:
        put(client, ctx(client, approved=False))
    assert error.value.status_code == 403


def test_the_upload_needs_a_target():
    client = _Client()
    with pytest.raises(HTTPException) as error:
        put(client, note_id=None)
    assert error.value.status_code == 422


def test_anonymous_download_is_refused():
    from fastapi.testclient import TestClient

    from app.main import app

    http = TestClient(app)
    assert http.get("/files/download?file_id=1").status_code == 401
    assert http.post("/files/upload?name=a.pdf&note_id=1", content=b"%PDF").status_code == 401
    assert http.post("/files/delete", json={"file_id": 1}).status_code == 401


def test_a_page_file_downloads_for_any_approved_user_and_a_note_file_for_its_author():
    client = _Client()
    note_file = put(client)
    page_file = put(client, ctx(client, "a1", "admin"), node_id=20, note_id=None)

    link = download_file(ctx(client), FileIdParams(file_id=note_file["id"]))
    assert link["url"].startswith("https://storage/notes/1/") and link["name"] == "notes.pdf"
    assert download_file(ctx(client, "u2"), FileIdParams(file_id=page_file["id"]))["url"]

    with pytest.raises(HTTPException) as error:
        download_file(ctx(client, "u2"), FileIdParams(file_id=note_file["id"]))
    assert error.value.status_code == 404
    assert download_file(ctx(client, "a1", "admin"), FileIdParams(file_id=note_file["id"]))["url"]
    with pytest.raises(HTTPException) as error:
        download_file(ctx(client, "u2", approved=False), FileIdParams(file_id=page_file["id"]))
    assert error.value.status_code == 403


def test_the_author_removes_a_file_while_pending_and_an_admin_a_page_file():
    client = _Client()
    mine = put(client)
    page = put(client, ctx(client, "a1", "admin"), node_id=20, note_id=None)

    with pytest.raises(HTTPException) as error:
        delete_file(ctx(client, "u2"), FileIdParams(file_id=mine["id"]))
    assert error.value.status_code == 404
    with pytest.raises(HTTPException) as error:
        delete_file(ctx(client), FileIdParams(file_id=page["id"]))
    assert error.value.status_code == 403

    delete_file(ctx(client), FileIdParams(file_id=mine["id"]))
    delete_file(ctx(client, "a1", "admin"), FileIdParams(file_id=page["id"]))
    assert client.files.rows == [] and client.bucket.objects == {}


def test_a_closed_notes_files_stay():
    client = _Client()
    mine = put(client)
    client.notes.rows[0]["status"] = "processed"
    with pytest.raises(HTTPException) as error:
        delete_file(ctx(client), FileIdParams(file_id=mine["id"]))
    assert error.value.status_code == 409


def test_the_list_of_a_note_is_for_its_author():
    client = _Client()
    put(client)
    assert len(note_files(ctx(client), NoteFilesParams(note_id=1))) == 1
    with pytest.raises(HTTPException) as error:
        note_files(ctx(client, "u2"), NoteFilesParams(note_id=1))
    assert error.value.status_code == 404


# --- before the migration ---


def test_without_the_migration_it_says_so_and_pages_still_read():
    client = _Client(missing=True)
    with pytest.raises(HTTPException) as error:
        put(client)
    assert error.value.status_code == 503 and "not set up" in error.value.detail
    assert not client.bucket.objects
    assert node_files(client, 20) == []


# --- the pass ---


def _zip(*names):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name in names:
            archive.writestr(name, "x")
    return buffer.getvalue()


def test_the_peek_lists_a_zip_and_starts_a_text_file():
    assert peek("p.zip", _zip("src/a.py", "README.md")) == "Entries: src/a.py, README.md"
    assert peek("a.py", b"print('hi')") == "print('hi')"
    assert peek("a.pdf", b"%PDF") == ""
    assert peek("bad.zip", b"nope") == ""


NODES = [
    {"id": 10, "parent_id": None, "kind": "section", "title": "Tools", "position": 0},
    {"id": 20, "parent_id": 10, "kind": "page", "title": "Git", "position": 0},
]
FILES = [
    {"id": 5, "note_id": 1, "name": "demo.zip", "kind": "zip", "size": 900, "peek": "Entries: a.py"},
    {"id": 6, "note_id": 1, "name": "cat.png", "kind": "image", "size": 50, "peek": ""},
]
NOTE = {"id": 1, "content": "my demo", "node_id": 20, "status": "pending", "files": FILES}


def test_the_gatekeeper_gets_each_notes_files():
    llm = FakeLLM()
    run_gatekeeper(llm, [NOTE], NODES, language="en")
    user = llm.calls[0][2]
    assert '"name": "demo.zip"' in user and '"peek": "Entries: a.py"' in user
    assert '"kind": "image"' in user and "path" not in user
    assert "files" not in _notes([{"id": 2, "content": "no files"}])[0]


def test_read_page_lists_the_pages_files():
    pages = {20: {"id": 20, "title": "Git", "content_md": "# Git", "files": [{"name": "guide.pdf"}]}}
    llm = FakeLLM(tool_rounds=[[("read_page", {"node_id": 20})]])
    run_gatekeeper(llm, [NOTE], NODES, read_page=pages.get, language="en")
    assert llm.tool_results[0].endswith("Files: guide.pdf")


def _pass(plan):
    store = FakeStore(notes=[NOTE], nodes=NODES, pages=[{"id": 20, "title": "Git", "content_md": ""}])
    llm = FakeLLM(json_response=plan, text_response="# Git\n\nNotes.")
    stats = run_daily_pass(store=store, llm=llm, language="en")
    return store, stats


def test_a_kept_file_goes_to_the_page_and_a_discarded_one_to_the_log():
    store, stats = _pass({
        "batches": [{"note_ids": [1], "action": "update", "node_id": 20, "summary": "demo",
                     "reason": "a demo", "file_ids": [5]}],
        "discarded": [],
        "discarded_files": [{"file_id": 6, "reason": "a cat picture"}],
    })
    assert store.attached == [{"file_id": 5, "node_id": 20}]
    assert stats["files_attached"] == 1 and stats["files_discarded"] == 1
    reasons = [(e["action"], e["reason"]) for e in store.logs]
    assert ("updated", "File attached: demo.zip") in reasons
    assert ("discarded", "File cat.png: a cat picture") in reasons


def test_a_file_of_another_batch_or_unknown_is_not_attached():
    store = FakeStore(
        notes=[NOTE, {"id": 2, "content": "other", "status": "pending", "files": []}],
        nodes=NODES, pages=[{"id": 20, "title": "Git", "content_md": ""}],
    )
    plan = {"batches": [{"note_ids": [2], "action": "update", "node_id": 20, "summary": "x",
                         "file_ids": [5, 99]}], "discarded": []}
    run_daily_pass(store=store, llm=FakeLLM(json_response=plan, text_response="# Git"), language="en")
    assert store.attached == []
