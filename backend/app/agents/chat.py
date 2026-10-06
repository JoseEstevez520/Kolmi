from __future__ import annotations

import logging
from typing import Any, Callable

from ..class_settings import FALLBACK_LANGUAGE
from .client import LLM
from .prompts import CHAT_ACTIONS, CHAT_PASSAGES, chat_system
from .schemas import ChatAnswer
from .search import SEARCH_WEB_TOOL, WebSearch, search_tool, web_search
from .tree import READ_PAGE_TOOL, PageReader, build_index, read_page_tool

log = logging.getLogger(__name__)

# With passages, the most characters of tree index the chat is sent (some 1,500 tokens).
INDEX_BUDGET = 6000


def _combined_tool(read_page_run, search_run, action_run=None):
    """Dispatches a tool call to whichever of `read_page` and `search_web` is wired up, and any
    other to the registry's actions when given."""

    def run(name: str, args: dict[str, Any]) -> str:
        if name == "read_page":
            return read_page_run(name, args)
        if search_run is not None and name == "search_web":
            return search_run(name, args)
        if action_run is not None:
            return action_run(name, args)
        return f"There is no tool called {name}."

    return run


def run_chat(
    llm: LLM,
    question: str,
    nodes: list[dict[str, Any]],
    *,
    read_page: PageReader | None = None,
    language: str = FALLBACK_LANGUAGE,
    today: str = "",
    schedule: str = "",
    search: WebSearch | None = web_search,
    actions: list[dict[str, Any]] | None = None,
    run_action: Callable[[str, dict[str, Any]], str] | None = None,
    passages: list[dict[str, Any]] | None = None,
) -> ChatAnswer:
    """Answer a student's question from the class's own content, same shape as the gatekeeper:
    the tree as an index, and the pages it wants with the `read_page` tool. With a model that has
    no tools, or if that loop fails, it answers from the index alone. `schedule` is the week's
    timetable as plain text, already resolved against the tree's titles, and `today` its weekday
    and date; both empty when the class hasn't set a timetable up. `search` is a `search_web`
    reader, DuckDuckGo (needs no key) by default; pass `None` to turn it off. `actions` are the
    registry's tool schemas the asker is offered, and `run_action` runs or proposes one of them.
    `passages` are the chunks a search by meaning found closest to the question ({node_id, heading,
    content}), put before it; with them the index can be shortened, since they carry the content.
    """
    system = chat_system(language) + (f"\n\n{CHAT_ACTIONS}" if actions else "")
    when = f"\n\nToday: {today}" if today else ""
    timetable = f"\n\nTimetable:\n{schedule}" if schedule else ""
    index = build_index(nodes)
    found = ""
    if passages:
        system = f"{system}\n{CHAT_PASSAGES}"
        # Past the budget the index loses its descriptions, then its pages (a section's are a
        # read_page away), so it still fits as the notes grow.
        if len(index) > INDEX_BUDGET:
            index = build_index([{**n, "description": ""} for n in nodes])
        if len(index) > INDEX_BUDGET:
            index = build_index([n for n in nodes if n.get("kind") == "section"])
        titles = {n["id"]: n.get("title") or "" for n in nodes}
        parts = []
        for p in passages:
            title, heading = titles.get(p["node_id"], ""), p.get("heading") or ""
            # The breadcrumb often starts with the page's own title (its H1): said once.
            if heading == title or heading.startswith(f"{title} › "):
                heading = heading[len(title) + 3 :]
            label = " › ".join(part for part in (title, heading) if part)
            parts.append(f"[{p['node_id']} · {label}]\n{p['content']}")
        found = "\n\nPassages:\n\n" + "\n\n".join(parts)
    user = f"Tree:\n{index}{when}{timetable}{found}\n\nQuestion: {question}"

    with_tools = getattr(llm, "complete_with_tools", None)
    if with_tools is not None and read_page is not None:
        reads: list[int] = []
        queries: list[str] = []
        tools = [READ_PAGE_TOOL] + ([SEARCH_WEB_TOOL] if search is not None else [])
        tools += actions or []
        run_search = search_tool(search, queries) if search is not None else None
        run_tool = _combined_tool(read_page_tool(nodes, read_page, reads), run_search, run_action)
        try:
            raw = with_tools(system, user, tools, run_tool)
            return ChatAnswer.model_validate(raw)
        except Exception as exc:  # answer from the index alone rather than fail the question
            log.warning("chat tool loop failed, answering from the index: %s", exc)

    raw = llm.complete_json(system, user)
    return ChatAnswer.model_validate(raw).model_copy(update={"from_index": True})
