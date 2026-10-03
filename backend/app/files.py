"""Files: what may be attached, the checks, and the helpers the routes and the pass share.

The limits live here, in one place. The web keeps the same lists in `frontend/src/lib/files.js`
(for the picker's `accept` and size); the server is the one that decides.
"""

from __future__ import annotations

import mimetypes
import uuid
import zipfile
from contextlib import contextmanager
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any, Iterator

from fastapi import HTTPException
from postgrest.exceptions import APIError
from storage3.exceptions import StorageApiError

from .auth import Context

BUCKET = "files"
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_FILES_PER_NOTE = 5
DOWNLOAD_URL_SECONDS = 60

# Extension to kind. Nothing executable: no scripts for a shell, no binaries, no installers.
KINDS: dict[str, tuple[str, ...]] = {
    "zip": ("zip",),
    "pdf": ("pdf",),
    "image": ("png", "jpg", "jpeg", "gif", "webp", "bmp", "avif"),
    "text": ("txt", "md", "markdown", "rst", "log"),
    "data": ("json", "csv", "tsv", "xml"),
    "config": (
        "yml", "yaml", "toml", "ini", "cfg", "conf", "properties", "gradle", "lock", "gitignore",
    ),
    "code": (
        "py", "js", "mjs", "ts", "jsx", "tsx", "vue", "svelte", "html", "css", "scss", "java",
        "kt", "c", "h", "cpp", "hpp", "cs", "go", "rs", "rb", "php", "swift", "sql", "r", "lua",
        "dart", "ipynb",
    ),
}
EXTENSIONS: dict[str, str] = {ext: kind for kind, exts in KINDS.items() for ext in exts}

# What a browser may call each kind, besides the generic types it falls back to.
_GENERIC = ("", "application/octet-stream")
_MIMES: dict[str, tuple[str, ...]] = {
    "zip": ("application/zip", "application/x-zip-compressed", "application/x-zip"),
    "pdf": ("application/pdf",),
    "image": ("image/",),
    "text": ("text/",),
    "data": ("text/", "application/json", "application/xml", "application/csv",
             "application/vnd.ms-excel"),
    "config": ("text/", "application/x-yaml", "application/yaml", "application/toml"),
    "code": ("text/", "application/javascript", "application/typescript", "application/json",
             "application/x-httpd-php", "application/x-ipynb+json", "application/sql"),
}
_TEXT_KINDS = ("text", "data", "config", "code")
PEEK_CHARS = 1500
PEEK_ENTRIES = 40


def extension(name: str) -> str:
    return PurePosixPath(name).suffix.lstrip(".").lower() or PurePosixPath(name).name.lower().lstrip(".")


def kind_of(name: str) -> str | None:
    return EXTENSIONS.get(extension(name))


def check_file(name: str, mime: str, size: int, data: bytes | None = None) -> str:
    """Refuse what may not be attached; returns the file's kind."""
    kind = kind_of(name)
    if kind is None:
        raise HTTPException(415, "That kind of file can't be attached")
    mime = (mime or "").split(";")[0].strip().lower()
    if mime not in _GENERIC and not mime.startswith(_MIMES[kind]):
        raise HTTPException(415, "That kind of file can't be attached")
    if size <= 0:
        raise HTTPException(422, "The file is empty")
    if size > MAX_FILE_BYTES:
        raise HTTPException(413, f"Files can be up to {MAX_FILE_BYTES // (1024 * 1024)} MB")
    if data is not None:
        if kind == "zip" and not data.startswith(b"PK"):
            raise HTTPException(415, "That is not a zip file")
        if kind == "pdf" and not data.startswith(b"%PDF"):
            raise HTTPException(415, "That is not a PDF")
    return kind


def stored_mime(name: str, mime: str) -> str:
    mime = (mime or "").split(";")[0].strip().lower()
    if mime in _GENERIC:
        return mimetypes.guess_type(name)[0] or "application/octet-stream"
    return mime


def object_key(owner: str, name: str) -> str:
    """The key in the bucket: ASCII and unique, whatever the file is called."""
    ext = extension(name)
    return f"{owner}/{uuid.uuid4().hex}" + (f".{ext}" if ext.isalnum() else "")


def peek(name: str, data: bytes) -> str:
    """What the gatekeeper sees of a file: a zip's entries, or the start of a text or code file."""
    kind = kind_of(name)
    if kind == "zip":
        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                names = [i.filename for i in archive.infolist() if not i.is_dir()]
        except zipfile.BadZipFile:
            return ""
        more = f" (and {len(names) - PEEK_ENTRIES} more)" if len(names) > PEEK_ENTRIES else ""
        return "Entries: " + ", ".join(names[:PEEK_ENTRIES]) + more
    if kind in _TEXT_KINDS:
        return data[: PEEK_CHARS * 4].decode("utf-8", errors="replace")[:PEEK_CHARS]
    return ""


# --- Not set up yet --------------------------------------------------------------------------

NOT_SET_UP = "Files are not set up on this server yet: the files migration hasn't been applied"


def is_missing(exc: Exception) -> bool:
    """The `files` table or its bucket does not exist: the migration is not applied."""
    if isinstance(exc, APIError):
        message = exc.message or ""
        return exc.code in ("PGRST205", "42P01") or ("files" in message and "schema cache" in message)
    if isinstance(exc, StorageApiError):
        return "not found" in str(exc).lower() or "bucket" in str(exc).lower()
    return False


@contextmanager
def files_guard() -> Iterator[None]:
    """Turn a missing table or bucket into a clear 503."""
    try:
        yield
    except (APIError, StorageApiError) as exc:
        if is_missing(exc):
            raise HTTPException(503, NOT_SET_UP) from exc
        raise


def node_files(client: Any, node_id: int) -> list[dict[str, Any]]:
    """A page's files for the read model; none (not an error) until the migration is applied."""
    try:
        return (
            client.table("files")
            .select("id, name, size, mime, created_at")
            .eq("node_id", node_id)
            .order("id")
            .execute()
            .data
        )
    except APIError as exc:
        if is_missing(exc):
            return []
        raise


# --- Who may do what -------------------------------------------------------------------------


def approved(ctx: Context) -> None:
    if not ctx.profile or not ctx.profile.get("approved"):
        raise HTTPException(403, "Profile not approved")


def is_admin(ctx: Context) -> bool:
    return bool(ctx.profile and ctx.profile.get("role") == "admin")


def own_pending_note(ctx: Context, note_id: int) -> None:
    """The note is the caller's and the daily pass has not taken it. Anyone else's looks missing."""
    rows = (
        ctx.client.table("notes").select("id, user_id, status").eq("id", note_id).limit(1)
        .execute().data
    )
    if not rows or rows[0]["user_id"] != ctx.user_id:
        raise HTTPException(404, "Note not found")
    if rows[0]["status"] != "pending":
        raise HTTPException(409, "The daily pass already took this note")


def read_access(ctx: Context, file: dict[str, Any]) -> None:
    """Who may download: anyone approved for a page's file; a note's file, its author or an admin."""
    approved(ctx)
    if file.get("node_id") is not None or is_admin(ctx):
        return
    if file.get("user_id") != ctx.user_id:
        raise HTTPException(404, "File not found")
