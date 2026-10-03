from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from postgrest.exceptions import APIError

from . import files as filelib
from .class_settings import class_language, read_settings
from .supabase_client import get_client

NODE_COLUMNS = "id, parent_id, kind, title, description, icon, color, position, on_home"


class Store(Protocol):
    """Everything the daily pass reads and writes.

    The pass never talks to Supabase directly: it goes through this, so the
    whole flow can be tested with a fake store and no network.
    """

    def pending_notes(self) -> list[dict[str, Any]]: ...

    def class_language(self) -> str:
        """The language the notes and pages are written in (a code, like `en`)."""
        ...

    def nodes(self) -> list[dict[str, Any]]:
        """The tree, without the pages' text: the gatekeeper reads that with `page`."""
        ...

    def page(self, node_id: int) -> dict[str, Any] | None: ...

    def create_page(
        self,
        *,
        parent_id: int | None,
        title: str,
        description: str,
        placement: str = "last",
        after_node_id: int | None = None,
    ) -> dict[str, Any]: ...

    def save_version(self, node_id: int, content_md: str, content_web: str) -> None: ...

    def write_page(self, node_id: int, *, content_md: str, content_web: str) -> None: ...

    def set_note_status(self, note_id: int, status: str) -> None: ...

    def attach_file(self, file_id: int, node_id: int, note_ids: list[int]) -> bool:
        """Move a note's file to a page, if it is one of `note_ids`'s. False when it isn't."""
        ...

    def log(
        self,
        *,
        pass_id: int,
        note_id: int | None,
        node_id: int | None,
        action: str,
        reason: str,
    ) -> None: ...

    def flag_counts(self, note_ids: list[int], reason: str) -> dict[int, int]:
        """How many `flagged` rows with this reason each note has in `ai_log`."""
        ...

    def open_pass(self, model: str) -> int: ...

    def close_pass(
        self,
        pass_id: int,
        *,
        status: str,
        stats: dict[str, Any],
        error: str | None = None,
    ) -> None: ...

    def running_pass(self, stale_minutes: int) -> dict[str, Any] | None: ...

    def schedule(self) -> dict[str, Any]:
        """The class settings, with the pass's schedule."""
        ...

    def last_pass_started(self) -> datetime | None:
        """When the latest pass, finished or not, started."""
        ...


def place_among(
    siblings: list[dict[str, Any]], placement: str, after_node_id: int | None
) -> tuple[int, dict[int, int]]:
    """Where a new node goes among its siblings: its position, and the siblings that move.

    `placement` is "first", "after" (the sibling `after_node_id`) or "last". Anything else, or
    an id that is not a sibling, means the end. Positions come out contiguous from 0.
    """
    order = [s["id"] for s in sorted(siblings, key=lambda s: s.get("position") or 0)]
    slot = len(order)
    if placement == "first":
        slot = 0
    elif placement == "after" and after_node_id in order:
        slot = order.index(after_node_id) + 1
    current = {s["id"]: s.get("position") for s in siblings}
    moves = {}
    for i, node_id in enumerate(order):
        target = i if i < slot else i + 1
        if current[node_id] != target:
            moves[node_id] = target
    return slot, moves


class SupabaseStore:
    """The real store: a Supabase client with the service role key."""

    def __init__(self, client=None) -> None:
        self.client = client or get_client()

    def class_language(self) -> str:
        return class_language(self.client)

    def pending_notes(self) -> list[dict[str, Any]]:
        notes = (
            self.client.table("notes")
            .select("id, content, node_id, user_id, created_at")
            .eq("status", "pending")
            .order("created_at")
            .execute()
            .data
        )
        return self._with_files(notes)

    def _with_files(self, notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Each note with its files, and for each what the gatekeeper can see of it."""
        if not notes:
            return notes
        try:
            rows = (
                self.client.table("files")
                .select("id, note_id, name, size, mime, path")
                .in_("note_id", [n["id"] for n in notes])
                .order("id")
                .execute()
                .data
            )
        except APIError as exc:
            if filelib.is_missing(exc):
                return notes
            raise
        for note in notes:
            note["files"] = []
        by_id = {n["id"]: n for n in notes}
        for row in rows:
            try:
                data = self.client.storage.from_(filelib.BUCKET).download(row["path"])
                peek = filelib.peek(row["name"], data)
            except Exception:  # the file is listed without a peek
                peek = ""
            by_id[row["note_id"]]["files"].append(
                {**row, "kind": filelib.kind_of(row["name"]), "peek": peek}
            )
        return notes

    def attach_file(self, file_id: int, node_id: int, note_ids: list[int]) -> bool:
        # The file leaves its note: the page owns it now, and the note going away leaves it be.
        rows = (
            self.client.table("files")
            .update({"node_id": node_id, "note_id": None})
            .eq("id", file_id)
            .in_("note_id", note_ids)
            .execute()
            .data
        )
        return bool(rows)

    def nodes(self) -> list[dict[str, Any]]:
        return (
            self.client.table("nodes")
            .select(NODE_COLUMNS)
            .order("position")
            .execute()
            .data
        )

    def page(self, node_id: int) -> dict[str, Any] | None:
        rows = (
            self.client.table("nodes")
            .select("id, title, content_md, content_web")
            .eq("id", node_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        return {**rows[0], "files": filelib.node_files(self.client, node_id)}

    def create_page(
        self,
        *,
        parent_id: int | None,
        title: str,
        description: str,
        placement: str = "last",
        after_node_id: int | None = None,
    ) -> dict[str, Any]:
        query = self.client.table("nodes").select("id, position").order("position")
        query = query.is_("parent_id", "null") if parent_id is None else query.eq(
            "parent_id", parent_id
        )
        siblings = query.execute().data
        slot, moves = place_among(siblings, placement, after_node_id)
        for node_id, position in moves.items():
            self.client.table("nodes").update({"position": position}).eq("id", node_id).execute()
        return (
            self.client.table("nodes")
            .insert(
                {
                    "parent_id": parent_id,
                    "kind": "page",
                    "title": title,
                    "description": description,
                    "position": slot,
                }
            )
            .execute()
            .data[0]
        )

    def save_version(self, node_id: int, content_md: str, content_web: str) -> None:
        self.client.table("node_versions").insert(
            {"node_id": node_id, "content_md": content_md, "content_web": content_web}
        ).execute()

    def write_page(self, node_id: int, *, content_md: str, content_web: str) -> None:
        self.client.table("nodes").update(
            {
                "content_md": content_md,
                "content_web": content_web,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", node_id).execute()

    def set_note_status(self, note_id: int, status: str) -> None:
        self.client.table("notes").update({"status": status}).eq("id", note_id).execute()

    def log(
        self,
        *,
        pass_id: int,
        note_id: int | None,
        node_id: int | None,
        action: str,
        reason: str,
    ) -> None:
        self.client.table("ai_log").insert(
            {
                "pass_id": pass_id,
                "note_id": note_id,
                "node_id": node_id,
                "action": action,
                "reason": reason,
            }
        ).execute()

    def flag_counts(self, note_ids: list[int], reason: str) -> dict[int, int]:
        if not note_ids:
            return {}
        rows = (
            self.client.table("ai_log")
            .select("note_id")
            .eq("action", "flagged")
            .eq("reason", reason)
            .in_("note_id", note_ids)
            .execute()
            .data
        )
        counts: dict[int, int] = {}
        for row in rows:
            counts[row["note_id"]] = counts.get(row["note_id"], 0) + 1
        return counts

    def open_pass(self, model: str) -> int:
        row = (
            self.client.table("ai_passes")
            .insert({"status": "running", "model": model})
            .execute()
            .data[0]
        )
        return row["id"]

    def close_pass(
        self,
        pass_id: int,
        *,
        status: str,
        stats: dict[str, Any],
        error: str | None = None,
    ) -> None:
        self.client.table("ai_passes").update(
            {
                "status": status,
                "stats": stats,
                "error": error,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", pass_id).execute()

    def running_pass(self, stale_minutes: int) -> dict[str, Any] | None:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)).isoformat()
        rows = (
            self.client.table("ai_passes")
            .select("id, started_at")
            .eq("status", "running")
            .gte("started_at", cutoff)
            .limit(1)
            .execute()
            .data
        )
        return rows[0] if rows else None

    def schedule(self) -> dict[str, Any]:
        return read_settings(self.client)

    def last_pass_started(self) -> datetime | None:
        rows = (
            self.client.table("ai_passes")
            .select("started_at")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        return datetime.fromisoformat(rows[0]["started_at"]) if rows else None
