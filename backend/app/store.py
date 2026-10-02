from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from .supabase_client import get_client

NODE_COLUMNS = "id, parent_id, kind, title, description, icon, color, position, on_home"


class Store(Protocol):
    """Everything the daily pass reads and writes.

    The pass never talks to Supabase directly: it goes through this, so the
    whole flow can be tested with a fake store and no network.
    """

    def pending_notes(self) -> list[dict[str, Any]]: ...

    def nodes(self) -> list[dict[str, Any]]: ...

    def page(self, node_id: int) -> dict[str, Any] | None: ...

    def create_page(
        self, *, parent_id: int | None, title: str, description: str
    ) -> dict[str, Any]: ...

    def save_version(self, node_id: int, content_md: str, content_web: str) -> None: ...

    def write_page(self, node_id: int, *, content_md: str, content_web: str) -> None: ...

    def set_note_status(self, note_id: int, status: str) -> None: ...

    def log(
        self,
        *,
        pass_id: int,
        note_id: int | None,
        node_id: int | None,
        action: str,
        reason: str,
    ) -> None: ...

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


class SupabaseStore:
    """The real store: a Supabase client with the service role key."""

    def __init__(self, client=None) -> None:
        self.client = client or get_client()

    def pending_notes(self) -> list[dict[str, Any]]:
        return (
            self.client.table("notes")
            .select("id, content, node_id, user_id, created_at")
            .eq("status", "pending")
            .order("created_at")
            .execute()
            .data
        )

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
        return rows[0] if rows else None

    def create_page(
        self, *, parent_id: int | None, title: str, description: str
    ) -> dict[str, Any]:
        query = (
            self.client.table("nodes").select("position").order("position", desc=True).limit(1)
        )
        query = query.is_("parent_id", "null") if parent_id is None else query.eq(
            "parent_id", parent_id
        )
        rows = query.execute().data
        position = rows[0]["position"] + 1 if rows else 0
        return (
            self.client.table("nodes")
            .insert(
                {
                    "parent_id": parent_id,
                    "kind": "page",
                    "title": title,
                    "description": description,
                    "position": position,
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
