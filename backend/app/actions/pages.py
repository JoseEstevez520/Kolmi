import logging
import threading
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..agents.client import get_llm, get_web_llm
from ..agents.notes import write_markdown
from ..agents.tree import build_index
from ..agents.web import build_page
from ..auth import Context
from ..class_settings import class_language
from ..store import NODE_COLUMNS, SupabaseStore
from .registry import action

log = logging.getLogger(__name__)


class WritePageParams(BaseModel):
    node_id: int = Field(..., description="The page to write, from list_nodes. It must be a page, not a section.")
    markdown: str = Field(
        ...,
        min_length=1,
        max_length=200_000,
        description="The Markdown to put in the page: the whole page in replace mode, the material to fold in in merge mode.",
    )
    mode: Literal["replace", "merge"] = Field(
        ...,
        description="replace: the Markdown becomes the page as it is. merge: the notes agent folds it into what the page already has, stripping names and private data.",
    )
    source_url: str | None = Field(
        None,
        max_length=2000,
        description="Where the material comes from (a Moodle page, a repo, a forum thread), if anywhere. It goes in the AI log.",
    )


class PageIdParams(BaseModel):
    node_id: int = Field(..., description="The page, from list_nodes. It must be a page, not a section.")


def check_page(ctx: Context, node_id: int, tool: str) -> dict[str, Any]:
    """The node as a row, or the error that says how to recover: it is missing or a section."""
    rows = ctx.client.table("nodes").select("id, kind").eq("id", node_id).limit(1).execute().data
    if not rows:
        raise HTTPException(404, f"There is no node {node_id}; list_nodes shows the tree")
    if rows[0]["kind"] != "page":
        raise HTTPException(
            422, f"Node {node_id} is a section; {tool} writes pages. create_node makes one"
        )
    return rows[0]


def _log(client, node_id: int, action_: str, reason: str, user_id: str, source: str) -> None:
    client.table("ai_log").insert(
        {
            "node_id": node_id,
            "action": action_,
            "reason": reason,
            "user_id": user_id,
            "source": source,
        }
    ).execute()


def rewrite_page(
    client,
    *,
    node_id: int,
    markdown: str,
    mode: str,
    user_id: str,
    source: str,
    source_url: str | None = None,
    llm=None,
    web_llm=None,
) -> None:
    """Write a page's Markdown and web outside the daily pass; never raises.

    `replace` takes the Markdown as given, `merge` has the notes agent fold it into the page
    (and strip names and private data), `rebuild` keeps the page's Markdown and only makes its
    web again. The previous content is kept as a version. The outcome goes to `ai_log`.
    """
    try:
        llm = llm or get_llm()
        web_llm = web_llm if web_llm is not None else get_web_llm()
        rows = (
            client.table("nodes")
            .select("id, title, content_md, content_web")
            .eq("id", node_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            raise ValueError(f"there is no node {node_id}")
        node = rows[0]
        existing_md = node.get("content_md") or ""
        existing_web = node.get("content_web") or ""
        language = class_language(client)
        index = build_index(client.table("nodes").select(NODE_COLUMNS).order("position").execute().data)

        if mode == "replace":
            md = markdown
        elif mode == "merge":
            md, _ = write_markdown(
                llm,
                title=node["title"],
                summary=markdown,
                existing_md=existing_md,
                language=language,
                index=index,
            )
            md = md or existing_md
        else:
            md = existing_md

        written = build_page(
            llm,
            web_llm,
            title=node["title"],
            markdown=md,
            existing_web=existing_web,
            language=language,
            index=index,
        )

        store = SupabaseStore(client)
        if existing_md.strip() or existing_web.strip():
            store.save_version(node_id, existing_md, existing_web)
        store.write_page(node_id, content_md=md, content_web=written.content_web)

        if mode == "rebuild":
            reason = "Rebuilt from its Markdown"
        else:
            reason = f"Written from outside the pass ({mode})"
            if source_url:
                reason += f" from {source_url}"
        _log(client, node_id, "updated", reason, user_id, source)
    except Exception as exc:  # it runs in a thread: the log is where the failure shows
        log.warning("could not write page %s: %s", node_id, exc)
        try:
            _log(client, node_id, "flagged", f"Could not write the page: {exc}", user_id, source)
        except Exception:
            log.exception("could not log the failure of page %s", node_id)


def start_rewrite(client, **kwargs: Any) -> None:
    """Run `rewrite_page` in the background, as run_pass does with the pass."""
    threading.Thread(
        target=rewrite_page, args=(client,), kwargs=kwargs, daemon=True
    ).start()


@action(
    name="write_page",
    tool=True,
    mcp=True,
    description="Put Markdown into a page. replace: the Markdown becomes the page as it is, past the gatekeeper and the name stripping, so use it for text you wrote yourself. merge: the notes agent folds it into what the page has and strips names and private data, so use it for material from Moodle, a repo or a forum. Admin only. It runs in the background and answers at once; the page keeps its previous content as a version, and view_ai_log shows when it is done (or why it failed).",
    params=WritePageParams,
    path="/page/write",
    min_role="admin",
)
def write_page(ctx: Context, params: WritePageParams):
    check_page(ctx, params.node_id, "write_page")
    start_rewrite(
        ctx.client,
        node_id=params.node_id,
        markdown=params.markdown,
        mode=params.mode,
        user_id=ctx.user_id,
        source=ctx.source,
        source_url=params.source_url,
    )
    return {"status": "queued", "node_id": params.node_id}
