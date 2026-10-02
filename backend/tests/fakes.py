from __future__ import annotations

from typing import Any


class FakeLLM:
    """A model that answers with whatever the test hands it."""

    model = "fake"

    def __init__(
        self,
        json_response: dict[str, Any] | None = None,
        text_response: str = "",
    ) -> None:
        self.json_response = json_response or {"batches": [], "discarded": []}
        self.text_response = text_response
        self.calls: list[tuple[str, str, str]] = []

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        self.calls.append(("json", system, user))
        return self.json_response

    def complete_text(self, system: str, user: str) -> str:
        self.calls.append(("text", system, user))
        return self.text_response


class FakeStore:
    """The daily pass's IO, in memory."""

    def __init__(
        self,
        notes: list[dict[str, Any]] | None = None,
        nodes: list[dict[str, Any]] | None = None,
        pages: list[dict[str, Any]] | None = None,
    ) -> None:
        self._notes = {n["id"]: dict(n) for n in (notes or [])}
        self._nodes = list(nodes or [])
        self._pages = {p["id"]: dict(p) for p in (pages or [])}
        self._next_id = max([*self._pages, 0]) + 1
        self.versions: list[dict[str, Any]] = []
        self.logs: list[dict[str, Any]] = []
        self.passes: dict[int, dict[str, Any]] = {}

    def pending_notes(self) -> list[dict[str, Any]]:
        return [dict(n) for n in self._notes.values() if n["status"] == "pending"]

    def nodes(self) -> list[dict[str, Any]]:
        return list(self._nodes)

    def page(self, node_id: int) -> dict[str, Any] | None:
        return dict(self._pages[node_id]) if node_id in self._pages else None

    def create_page(
        self, *, parent_id: int | None, title: str, description: str
    ) -> dict[str, Any]:
        node_id = self._next_id
        self._next_id += 1
        page = {"id": node_id, "title": title, "content_md": "", "content_web": ""}
        self._pages[node_id] = page
        return dict(page)

    def save_version(self, node_id: int, content_md: str, content_web: str) -> None:
        self.versions.append(
            {"node_id": node_id, "content_md": content_md, "content_web": content_web}
        )

    def write_page(self, node_id: int, *, content_md: str, content_web: str) -> None:
        self._pages[node_id]["content_md"] = content_md
        self._pages[node_id]["content_web"] = content_web

    def set_note_status(self, note_id: int, status: str) -> None:
        self._notes[note_id]["status"] = status

    def log(
        self,
        *,
        pass_id: int,
        note_id: int | None,
        node_id: int | None,
        action: str,
        reason: str,
    ) -> None:
        self.logs.append(
            {
                "pass_id": pass_id,
                "note_id": note_id,
                "node_id": node_id,
                "action": action,
                "reason": reason,
            }
        )

    def flag_counts(self, note_ids: list[int], reason: str) -> dict[int, int]:
        counts: dict[int, int] = {}
        for entry in self.logs:
            if (
                entry["action"] == "flagged"
                and entry["reason"] == reason
                and entry["note_id"] in note_ids
            ):
                counts[entry["note_id"]] = counts.get(entry["note_id"], 0) + 1
        return counts

    def open_pass(self, model: str) -> int:
        pass_id = len(self.passes) + 1
        self.passes[pass_id] = {"id": pass_id, "status": "running", "model": model}
        return pass_id

    def close_pass(
        self,
        pass_id: int,
        *,
        status: str,
        stats: dict[str, Any],
        error: str | None = None,
    ) -> None:
        self.passes[pass_id].update({"status": status, "stats": stats, "error": error})

    def running_pass(self, stale_minutes: int) -> dict[str, Any] | None:
        for item in self.passes.values():
            if item["status"] == "running":
                return item
        return None
