from __future__ import annotations

from ..class_settings import FALLBACK_LANGUAGE
from .client import LLM
from .prompts import notes_system, tree_lines

# Where the agent's account of its own decisions starts, after the page.
DECISIONS_MARK = "---decisions---"


def write_markdown(
    llm: LLM,
    *,
    title: str,
    summary: str,
    existing_md: str = "",
    language: str = FALLBACK_LANGUAGE,
    index: str = "",
) -> tuple[str, str]:
    """Write (or update) the page's Markdown, its source, in the class `language`.

    `summary` is the gatekeeper's: what the notes add to the page, sanitized. `index` is the
    tree's (`build_index`), so the page can link to the others. Returns the Markdown and the
    agent's account of what it left out or changed and why (empty when it gave none).
    """
    parts = [f"Page title: {title}", "", "New material for the page:", summary]
    if existing_md.strip():
        parts += ["", "Current page, in Markdown (fold the new material in):", existing_md]
    parts += tree_lines(index)
    answer = llm.complete_text(notes_system(language), "\n".join(parts))
    markdown, _, decisions = answer.partition(DECISIONS_MARK)
    return markdown.strip(), decisions.strip()
