from __future__ import annotations

from ..class_settings import FALLBACK_LANGUAGE
from .client import LLM
from .prompts import notes_system


def write_markdown(
    llm: LLM,
    *,
    title: str,
    summary: str,
    existing_md: str = "",
    language: str = FALLBACK_LANGUAGE,
) -> str:
    """Write (or update) the page's Markdown in the house style, in the class `language`."""
    parts = [f"Page title: {title}", "", "Sanitized summary of the new notes:", summary]
    if existing_md.strip():
        parts += ["", "Current page Markdown (keep what still holds):", existing_md]
    return llm.complete_text(notes_system(language), "\n".join(parts)).strip()
