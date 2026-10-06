import logging
import threading
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..agents.client import get_llm, get_web_llm
from ..agents.notes import write_markdown
from ..agents.tree import build_index
from ..agents import openui
from ..agents.web import build_page, page_problems
from ..auth import Context
from ..class_settings import class_language
from ..rag import index_pages
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


class WritePageWebParams(BaseModel):
    node_id: int = Field(..., description="The page to write, from list_nodes. It must be a page, not a section.")
    content_web: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="The whole page in OpenUI Lang, starting root = Page([...]), with every Diagram's svg and every Artifact's piece already drawn. view_node with include_web gives the current one, to change what is there.",
    )
    source_url: str | None = Field(
        None,
        max_length=2000,
        description="Where the page or its pieces come from, if anywhere. It goes in the AI log.",
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
        # A rebuild keeps the Markdown, so its hash matches and nothing is embedded again.
        index_pages(client, [node_id])

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


class VersionIdParams(BaseModel):
    version_id: int = Field(..., description="The version to restore, from list_versions.")


@action(
    name="rebuild_page",
    tool=True,
    mcp=True,
    description="Make a page's web again from its current Markdown, without changing the Markdown. Admin only. Use it when the page looks wrong but its text is right. It runs in the background and answers at once; the page keeps its previous content as a version, and view_ai_log shows when it is done.",
    params=PageIdParams,
    path="/page/rebuild",
    min_role="admin",
)
def rebuild_page(ctx: Context, params: PageIdParams):
    check_page(ctx, params.node_id, "rebuild_page")
    start_rewrite(
        ctx.client,
        node_id=params.node_id,
        markdown="",
        mode="rebuild",
        user_id=ctx.user_id,
        source=ctx.source,
    )
    return {"status": "queued", "node_id": params.node_id}


@action(
    name="list_versions",
    read_only=True,
    tool=True,
    mcp=True,
    description="The earlier versions of a page, newest first: id, when it was saved and the start of its Markdown as a preview. Admin only. A version is saved each time a page is rewritten; restore_version brings one back.",
    params=PageIdParams,
    method="GET",
    path="/page/versions",
    min_role="admin",
)
def list_versions(ctx: Context, params: PageIdParams):
    rows = (
        ctx.client.table("node_versions")
        .select("id, created_at, content_md")
        .eq("node_id", params.node_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    return [
        {"id": r["id"], "created_at": r["created_at"], "preview": (r.get("content_md") or "")[:300]}
        for r in rows
    ]


@action(
    name="restore_version",
    tool=True,
    mcp=True,
    description="Put an earlier version of a page back, from list_versions. Admin only, confirmed. The page as it is now is saved as a version first, so a restore can be undone.",
    params=VersionIdParams,
    path="/page/versions/restore",
    requires_confirmation=True,
    min_role="admin",
)
def restore_version(ctx: Context, params: VersionIdParams):
    rows = (
        ctx.client.table("node_versions")
        .select("id, node_id, content_md, content_web")
        .eq("id", params.version_id)
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(
            404, f"There is no version {params.version_id}; list_versions lists a page's"
        )
    version = rows[0]
    node_id = version["node_id"]
    store = SupabaseStore(ctx.client)
    current = store.page(node_id)
    if current and ((current.get("content_md") or "").strip() or (current.get("content_web") or "").strip()):
        store.save_version(node_id, current.get("content_md") or "", current.get("content_web") or "")
    store.write_page(
        node_id,
        content_md=version.get("content_md") or "",
        content_web=version.get("content_web") or "",
    )
    index_pages(ctx.client, [node_id])
    _log(ctx.client, node_id, "updated", f"Restored version {params.version_id}", ctx.user_id, ctx.source)
    return ctx.client.table("nodes").select(NODE_COLUMNS).eq("id", node_id).limit(1).execute().data[0]


@action(
    name="write_page_web",
    tool=True,
    mcp=True,
    description="Set a page's web, its OpenUI Lang, exactly as given, with no web agent in between: for a livelier page than the agent makes (a richer figure, a chart, an interactive piece). Admin only, confirmed. It is checked against the catalogue first and nothing is saved if it fails: the error lists each line and what to change, so fix those and send the whole page again. To change what is there rather than write it all, read it first with view_node and include_web. The page's Markdown stays as it is and its previous web is kept as a version (list_versions, restore_version). The web follows the Markdown: the page's next rebuild draws it again from there.",
    params=WritePageWebParams,
    path="/page/web",
    requires_confirmation=True,
    min_role="admin",
)
def write_page_web(ctx: Context, params: WritePageWebParams):
    check_page(ctx, params.node_id, "write_page_web")
    found = page_problems(params.content_web)
    if found:
        listed = "\n".join(f"- {problem}" for problem in found)
        raise HTTPException(
            422,
            f"The page's OpenUI Lang doesn't hold up, so nothing was saved:\n{listed}\n"
            "Fix these and send the whole page again.",
        )

    store = SupabaseStore(ctx.client)
    rows = (
        ctx.client.table("nodes")
        .select("content_md, content_web")
        .eq("id", params.node_id)
        .limit(1)
        .execute()
        .data
    )
    current = rows[0] if rows else {}
    existing_md = current.get("content_md") or ""
    existing_web = current.get("content_web") or ""
    if existing_md.strip() or existing_web.strip():
        store.save_version(params.node_id, existing_md, existing_web)
    # The Markdown stays as it is: the page's source, for the chat and the next rebuild.
    store.write_page(
        params.node_id, content_md=existing_md, content_web=openui.strip_fence(params.content_web)
    )
    reason = "Web written as given"
    if params.source_url:
        reason += f" from {params.source_url}"
    _log(ctx.client, params.node_id, "updated", reason, ctx.user_id, ctx.source)
    return (
        ctx.client.table("nodes").select(NODE_COLUMNS).eq("id", params.node_id).limit(1).execute().data[0]
    )
