from __future__ import annotations

import logging
from dataclasses import dataclass

from . import openui
from .client import LLM
from .notes import write_markdown

log = logging.getLogger(__name__)


@dataclass
class Page:
    """What gets written to a page, and how it was made."""

    content_md: str
    content_web: str
    # "web" when the web agent wrote OpenUI Lang, "markdown" when the notes agent wrote it.
    source: str
    # Why the web agent was skipped or failed, when it was.
    fallback_reason: str = ""


def _brief(*, title: str, summary: str, existing_md: str, existing_web: str) -> str:
    parts = [f"Page title: {title}", "", "Sanitized summary of the new notes:", summary]
    if existing_web.strip():
        parts += ["", "Current page, in OpenUI Lang (keep what still holds):", existing_web]
    elif existing_md.strip():
        parts += ["", "Current page, in Markdown (keep what still holds):", existing_md]
    return "\n".join(parts)


def write_web(
    web_llm: LLM, *, title: str, summary: str, existing_md: str = "", existing_web: str = ""
) -> Page:
    """Ask the web agent for the page in OpenUI Lang and derive its Markdown.

    Raises when the call fails or the answer is not a page.
    """
    brief = _brief(
        title=title, summary=summary, existing_md=existing_md, existing_web=existing_web
    )
    raw = web_llm.complete_text(openui.gateway_prompt(), brief)
    source = openui.strip_fence(raw)
    root = openui.parse(source)

    unknown = openui.unknown_components(root)
    if unknown:
        log.warning("page uses components outside the catalogue: %s", sorted(unknown))

    markdown = openui.to_markdown(root)
    if not markdown:
        raise openui.ParseError("the page has no content")
    return Page(content_md=markdown, content_web=source, source="web")


def build_page(
    llm: LLM,
    web_llm: LLM | None,
    *,
    title: str,
    summary: str,
    existing_md: str = "",
    existing_web: str = "",
) -> Page:
    """Write the page: OpenUI Lang through the web agent, or Markdown when that fails.

    The web agent (Thesys Gateway) writes `content_web`, and `content_md` is derived from it
    for the RAG. Without a web agent, or when it fails, the notes agent (DeepSeek) writes the
    Markdown alone and `content_web` is left empty, so the page shows its Markdown.
    """
    reason = "no web agent configured"
    if web_llm is not None:
        try:
            return write_web(
                web_llm,
                title=title,
                summary=summary,
                existing_md=existing_md,
                existing_web=existing_web,
            )
        except Exception as exc:  # any failure falls back; the pass goes on
            reason = f"web agent failed: {exc}"
            log.warning("%s; writing Markdown instead", reason)

    markdown = write_markdown(llm, title=title, summary=summary, existing_md=existing_md)
    return Page(
        content_md=markdown.strip(),
        content_web="",
        source="markdown",
        fallback_reason=reason,
    )
