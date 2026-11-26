"""A private activity feed, derived from the class's existing records."""
from datetime import datetime, timedelta, timezone

from ..auth import Context, app_only
from ..class_settings import read_settings
from .registry import action


@action(
    name="my_notifications", method="GET", path="/notifications", read_only=True,
    description="Read this member's recent class activity and replies to forum threads they participate in. App only.",
)
def my_notifications(ctx: Context, _params=None):
    app_only(ctx)
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    passes = (ctx.client.table("ai_passes").select("id, stats, started_at")
              .eq("status", "done").gte("started_at", since).order("started_at", desc=True).limit(100).execute().data)
    changed = {page.get("node_id") for run in passes for page in (run.get("stats") or {}).get("pages", [])}
    pages = []
    if changed:
        pages = (ctx.client.table("nodes").select("id, title, updated_at").in_("id", list(changed))
                 .eq("kind", "page").order("updated_at", desc=True).limit(200).execute().data)
    items = [dict(id=f"page:{p['id']}", kind="page", title=p["title"], at=p.get("updated_at"), href=f"/node/{p['id']}") for p in pages]
    if read_settings(ctx.client).get("forum_enabled", False):
        owned = ctx.client.table("forum_threads").select("id").eq("author_id", ctx.user_id).execute().data
        joined = ctx.client.table("forum_posts").select("thread_id").eq("author_id", ctx.user_id).execute().data
        threads = {t["id"] for t in owned} | {p["thread_id"] for p in joined}
        if threads:
            replies = (ctx.client.table("forum_posts").select("id, thread_id, author_id, created_at")
                       .in_("thread_id", list(threads)).gte("created_at", since)
                       .order("created_at", desc=True).limit(100).execute().data)
            for reply in replies:
                if reply.get("author_id") != ctx.user_id:
                    items.append(dict(id=f"reply:{reply['id']}", kind="reply", at=reply["created_at"], href=f"/forum/{reply['thread_id']}"))
    return {"since": since, "digest": {"passes": len(passes), "pages": len(pages)},
            "items": sorted(items, key=lambda item: item.get("at") or "", reverse=True)}
