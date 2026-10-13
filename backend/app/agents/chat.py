from __future__ import annotations

import logging
from typing import Any, Callable, Iterator

from ..class_settings import FALLBACK_LANGUAGE
from .client import LLM
from .prompts import CHAT_ACTIONS, CHAT_PASSAGES, CHAT_PASSAGES_STREAM, chat_stream_system, chat_system
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


def _prompt(
    system: str,
    question: str,
    nodes: list[dict[str, Any]],
    *,
    language: str,
    today: str,
    schedule: str,
    passages: list[dict[str, Any]] | None,
    history: list[dict[str, str]] | None,
    passages_note: str = CHAT_PASSAGES,
    page: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """The system prompt (with the passages' note when there are any) and the user message: the
    tree as an index, the day, the timetable, the passages, the conversation and the question."""
    when = f"\n\nToday: {today}" if today else ""
    timetable = f"\n\nTimetable:\n{schedule}" if schedule else ""
    index = build_index(nodes)
    found = ""
    if passages:
        system = f"{system}\n{passages_note}"
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
    said = ""
    if history:
        lines = [f"{'Student' if m['role'] == 'user' else 'You'}: {m['text']}" for m in history]
        said = "\n\nThe conversation so far, last message at the end:\n" + "\n".join(lines)
    # Only a pointer: the model reads the page itself if the question is about it.
    open_page = ""
    if page:
        open_page = (
            f"\n\nThe person has this page open: {page.get('title') or ''} (id {page['id']}). "
            "Read it with read_page if the question is about it."
        )
    user = f"Tree:\n{index}{when}{timetable}{found}{said}{open_page}\n\nQuestion: {question}"

    return system, user


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
    history: list[dict[str, str]] | None = None,
    page: dict[str, Any] | None = None,
) -> ChatAnswer:
    """Answer a student's question from the class's own content, same shape as the gatekeeper:
    the tree as an index, and the pages it wants with the `read_page` tool. With a model that has
    no tools, or if that loop fails, it answers from the index alone. `schedule` is the week's
    timetable as plain text, already resolved against the tree's titles, and `today` its weekday
    and date; both empty when the class hasn't set a timetable up. `search` is a `search_web`
    reader, DuckDuckGo (needs no key) by default; pass `None` to turn it off. `actions` are the
    registry's tool schemas the asker is offered, and `run_action` runs or proposes one of them.
    `page` is the node the person has open, if any (a pointer only). `passages` are the chunks a search by meaning found closest to the question ({node_id, heading,
    content}), put before it; with them the index can be shortened, since they carry the content.
    """
    system, user = _prompt(
        chat_system(language),
        question,
        nodes,
        language=language,
        today=today,
        schedule=schedule,
        passages=passages,
        history=history,
        page=page,
    )

    # The actions are told about only to the loop that can offer them: the answer from the index
    # alone has none, and would claim to have proposed what it can't.
    loop_system = system + (f"\n\n{CHAT_ACTIONS}" if actions else "")
    with_tools = getattr(llm, "complete_with_tools", None)
    if with_tools is not None and read_page is not None:
        reads: list[int] = []
        queries: list[str] = []
        tools = [READ_PAGE_TOOL] + ([SEARCH_WEB_TOOL] if search is not None else [])
        tools += actions or []
        run_search = search_tool(search, queries) if search is not None else None
        run_tool = _combined_tool(read_page_tool(nodes, read_page, reads), run_search, run_action)
        try:
            raw = with_tools(loop_system, user, tools, run_tool)
            return ChatAnswer.model_validate(raw)
        except Exception as exc:  # answer from the index alone rather than fail the question
            log.warning("chat tool loop failed, answering from the index: %s", exc)

    raw = llm.complete_json(system, user)
    return ChatAnswer.model_validate(raw).model_copy(update={"from_index": True})


def run_chat_stream(
    llm: LLM,
    question: str,
    nodes: list[dict[str, Any]],
    *,
    read_page: PageReader,
    language: str = FALLBACK_LANGUAGE,
    today: str = "",
    schedule: str = "",
    search: WebSearch | None = web_search,
    actions: list[dict[str, Any]] | None = None,
    run_action: Callable[[str, dict[str, Any]], str] | None = None,
    passages: list[dict[str, Any]] | None = None,
    history: list[dict[str, str]] | None = None,
    page: dict[str, Any] | None = None,
) -> Iterator[dict[str, str]]:
    """`run_chat`, streamed: the same context and tools, but the model writes an OpenUI Lang
    program (`root = Answer([...])`) and it comes out as `status` and `token` events as it is
    written. There is no fallback to the index alone: if the model fails, the error is the
    caller's to tell. Pages are read by the model's own `read_page`, so it gets no `sources` field;
    it cites them with a `Sources` part.
    """
    system, user = _prompt(
        chat_stream_system(language),
        question,
        nodes,
        language=language,
        today=today,
        schedule=schedule,
        passages=passages,
        history=history,
        passages_note=CHAT_PASSAGES_STREAM,
        page=page,
    )
    system += f"\n\n{CHAT_ACTIONS}" if actions else ""
    tools = [READ_PAGE_TOOL] + ([SEARCH_WEB_TOOL] if search is not None else [])
    tools += actions or []
    run_search = search_tool(search, []) if search is not None else None
    run_tool = _combined_tool(read_page_tool(nodes, read_page, []), run_search, run_action)
    yield from llm.stream_with_tools(system, user, tools, run_tool)
