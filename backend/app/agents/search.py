from __future__ import annotations

import logging
from typing import Any, Callable

log = logging.getLogger(__name__)

# A tool for the chat, not the pass: the only agent that needs the open web is the one a student
# is waiting on right now, for whatever the class's own content can't answer (today's date,
# something outside the class, current events). Backed by DuckDuckGo (`ddgs`), which needs no
# account or key, so it's simply always offered.

SEARCH_WEB_TOOL = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": (
            "Search the public web for something the class notes and timetable don't cover: "
            "current events, a fact outside the class, or anything else you don't already know."
        ),
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to search for."}},
            "required": ["query"],
        },
    },
}

WebSearch = Callable[[str], str]


def web_search(query: str) -> str:
    """A `search_web` reader backed by DuckDuckGo: a short query in, a few results' titles, URLs
    and snippets out, as plain text. A failed search never breaks the question: the model just
    answers without it.
    """
    try:
        from ddgs import DDGS

        results = DDGS().text(query, max_results=5)
    except Exception as exc:  # the package's own errors aren't typed; any failure degrades the same
        log.warning("web search failed: %s", exc)
        return "The search failed; answer without it."
    if not results:
        return "No results."
    return "\n\n".join(
        f"{r.get('title', '')}\n{r.get('href', '')}\n{(r.get('body') or '').strip()[:500]}"
        for r in results
    )


def search_tool(search: WebSearch, queries: list[str]) -> Callable[[str, dict[str, Any]], str]:
    """The `search_web` tool: each query goes in `queries`, so a pass can log what it looked up."""

    def run(name: str, args: dict[str, Any]) -> str:
        if name != "search_web":
            return f"There is no tool called {name}."
        query = str(args.get("query") or "").strip()
        if not query:
            return "search_web needs a query."
        queries.append(query)
        return search(query)

    return run
