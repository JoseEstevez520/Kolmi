"""Downloadable copies of shared pages and the caller's own raw notes."""

from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..auth import Context
from ..class_settings import read_settings
from ..export import build, build_notes, slugify, to_zip
from .registry import action


class ExportPagesParams(BaseModel):
    node_id: int | None = Field(default=None, description="Export this section or page, or the whole notebook when omitted.")


def _enabled(ctx: Context):
    if not read_settings(ctx.client)["export_enabled"]:
        raise HTTPException(403, "Export is disabled for this class")


def _zip(files: dict[str, str], name: str):
    if not files:
        raise HTTPException(404, "There is nothing to export yet")
    return Response(to_zip(files), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{name}.zip"'})


@action(name="export_pages", read_only=True, method="GET", path="/exports/pages",
        params=ExportPagesParams, description="Download shared pages as Markdown files with metadata. Export must be enabled by the class admin.")
def export_pages(ctx: Context, params: ExportPagesParams):
    _enabled(ctx)
    nodes = ctx.client.table("nodes").select("id, parent_id, kind, title, description, position, updated_at, content_md").execute().data
    try:
        files = build(nodes, params.node_id)
    except KeyError:
        raise HTTPException(404, "Node not found") from None
    name = "kolmi"
    if params.node_id is not None:
        node = next(n for n in nodes if n["id"] == params.node_id)
        name += "-" + slugify(node["title"], str(params.node_id))
    return _zip(files, name)


@action(name="export_notes", read_only=True, method="GET", path="/exports/notes",
        description="Download your own raw notes as Markdown files. Other students' notes and attachments are never included. Export must be enabled.")
def export_notes(ctx: Context, params: None):
    _enabled(ctx)
    notes = ctx.client.table("notes").select("id, content, format, status, node_id, created_at").eq("user_id", ctx.user_id).order("created_at").execute().data
    return _zip(build_notes(notes), "kolmi-my-notes")
