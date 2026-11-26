"""Compatibility route for the original shared notebook download."""

from fastapi import APIRouter, Depends

from .actions import get_action, invoke
from .auth import Context, get_context

router = APIRouter()


@router.get("/export", summary="Download shared pages as Markdown files.")
def export(node_id: int | None = None, ctx: Context = Depends(get_context)):
    return invoke(get_action("export_pages"), ctx, {"node_id": node_id})
