from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..auth import Context
from ..bugs import start_report
from ..class_settings import read_settings
from ..passes.schedule import today_start
from .registry import action

REPORT_COLUMNS = "id, title, status, page_path, verdict, issue_url, created_at"


class ReportBugParams(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="A short title for the problem.")
    body: str = Field(..., min_length=1, max_length=5000, description="What happened, what was expected and the steps to see it.")
    page_path: str | None = Field(None, max_length=500, description="The page of the app the person was on, like /node/12.")


def _within_the_cap(ctx: Context) -> None:
    """A student sends at most the class's daily number of reports: each costs a model call.
    Admins have no cap."""
    if (ctx.profile or {}).get("role") == "admin":
        return
    cap = read_settings(ctx.client).get("bug_report_daily_limit", 5)
    sent = (
        ctx.client.table("bug_reports")
        .select("id", count="exact")
        .eq("user_id", ctx.user_id)
        .gte("created_at", today_start())
        .execute()
    )
    if (sent.count or 0) >= cap:
        raise HTTPException(429, "You've reached today's limit for bug reports")


@action(
    name="report_bug",
    description="Report a problem with the app itself. It is judged in the background and, if genuine, becomes an issue for the maintainer. Answers at once with the report's id; my_bug_reports shows where it ended up.",
    params=ReportBugParams,
    path="/bugs",
)
def report_bug(ctx: Context, params: ReportBugParams):
    title, body = params.title.strip(), params.body.strip()
    if not title or not body:
        raise HTTPException(422, "Add a title and a description")
    _within_the_cap(ctx)
    row = (
        ctx.client.table("bug_reports")
        .insert(
            {
                "user_id": ctx.user_id,
                "title": title,
                "body": body,
                "page_path": params.page_path,
                "status": "pending",
            }
        )
        .execute()
        .data[0]
    )
    start_report(ctx.client, row["id"], title=title, body=body, page_path=params.page_path)
    return {"id": row["id"], "status": "queued"}


def _report(row: dict[str, Any]) -> dict[str, Any]:
    verdict = row.get("verdict") or {}
    return {
        "id": row["id"],
        "title": row["title"],
        "status": row["status"],
        "severity": verdict.get("severity"),
        "reason": verdict.get("reason"),
        "issue_url": row.get("issue_url"),
        "page_path": row.get("page_path"),
        "created_at": row.get("created_at"),
    }


@action(
    name="my_bug_reports",
    read_only=True,
    description="Your own bug reports, newest first, each with its status (pending, issue, discarded or failed), the reason it was judged that way and the issue link when there is one.",
    method="GET",
    path="/bugs/mine",
)
def my_bug_reports(ctx: Context, params: None):
    rows = (
        ctx.client.table("bug_reports")
        .select(REPORT_COLUMNS)
        .eq("user_id", ctx.user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
    )
    return [_report(r) for r in rows]
