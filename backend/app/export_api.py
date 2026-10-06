"""The export route: the class's shared pages as a zip of Markdown files."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from .auth import Context, app_only, check_active, get_context
from .export import build, slugify, to_zip

router = APIRouter()


@router.get("/export", summary="Download the shared pages as Markdown files, all or one section.")
def export(node_id: int | None = None, ctx: Context = Depends(get_context)):
    # Anyone in the class may take the shared pages. Raw notes and attachments never go in it.
    check_active(ctx)
    app_only(ctx)
    nodes = (
        ctx.client.table("nodes")
        .select("id, parent_id, kind, title, position, content_md")
        .execute()
        .data
    )
    try:
        files = build(nodes, node_id)
    except KeyError:
        raise HTTPException(404, "Node not found") from None
    if not files:
        raise HTTPException(404, "There are no pages to export here yet")
    name = "kolmi"
    if node_id is not None:
        name += "-" + slugify(next(n["title"] for n in nodes if n["id"] == node_id), str(node_id))
    return Response(
        to_zip(files),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}.zip"'},
    )
