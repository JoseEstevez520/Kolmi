from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class NewPage(BaseModel):
    parent_id: int | None = None
    title: str
    description: str = ""
    # Where it goes among its siblings: first, after the page `after_node_id`, or last.
    placement: Literal["first", "after", "last"] = "last"
    after_node_id: int | None = None
    placement_reason: str = ""


class Batch(BaseModel):
    """One group of notes that goes to one page."""

    note_ids: list[int] = Field(default_factory=list)
    action: Literal["create", "update"]
    node_id: int | None = None
    new_page: NewPage | None = None
    summary: str
    reason: str = ""
    # Files of those notes that stay: they are attached to the page.
    file_ids: list[int] = Field(default_factory=list)


class Discarded(BaseModel):
    note_id: int
    reason: str = ""


class DiscardedFile(BaseModel):
    file_id: int
    reason: str = ""


class GatekeeperResult(BaseModel):
    batches: list[Batch] = Field(default_factory=list)
    discarded: list[Discarded] = Field(default_factory=list)
    discarded_files: list[DiscardedFile] = Field(default_factory=list)
    # The nodes it read before deciding; filled in by the gatekeeper, not by the model.
    reads: list[int] = Field(default_factory=list, exclude=True)


class ChatAnswer(BaseModel):
    answer: str
    # The pages the answer actually rests on, so the app can show them as its sources.
    sources: list[int] = Field(default_factory=list)
