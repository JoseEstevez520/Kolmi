from __future__ import annotations

from .client import LLM
from .prompts import NOTES_SYSTEM


def write_markdown(
    llm: LLM, *, title: str, summary: str, existing_md: str = ""
) -> str:
    """Write (or update) the page's Markdown in the house style."""
    parts = [f"Page title: {title}", "", "Sanitized summary of the new notes:", summary]
    if existing_md.strip():
        parts += ["", "Current page Markdown (keep what still holds):", existing_md]
    return llm.complete_text(NOTES_SYSTEM, "\n".join(parts)).strip()
