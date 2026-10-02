from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class NewPage(BaseModel):
    parent_id: int | None = None
    title: str
    description: str = ""


class Batch(BaseModel):
    """One group of notes that goes to one page."""

    note_ids: list[int] = Field(default_factory=list)
    action: Literal["create", "update"]
    node_id: int | None = None
    new_page: NewPage | None = None
    summary: str
    reason: str = ""


class Discarded(BaseModel):
    note_id: int
    reason: str = ""


class GatekeeperResult(BaseModel):
    batches: list[Batch] = Field(default_factory=list)
    discarded: list[Discarded] = Field(default_factory=list)
    # The nodes it read before deciding; filled in by the gatekeeper, not by the model.
    reads: list[int] = Field(default_factory=list, exclude=True)
