from __future__ import annotations

import logging
from dataclasses import dataclass

from ..class_settings import FALLBACK_LANGUAGE
from . import openui
from .client import LLM
from .notes import write_markdown
from .prompts import language_line

log = logging.getLogger(__name__)


@dataclass
class Page:
    """What gets written to a page, and how it was made."""

    content_md: str
    content_web: str
    # "web" when it was written as OpenUI Lang, "markdown" when the notes agent wrote it.
    source: str
    # The model that wrote it.
    model: str = ""
    # Why the web model was not the one that wrote it, when it wasn't.
    fallback_reason: str = ""
    # Whether the web model was tried and failed, so the pass can stop asking it.
    web_failed: bool = False


def _brief(
    *, title: str, summary: str, existing_md: str, existing_web: str, language: str
) -> str:
    # The language goes in the brief: through the Gateway the system prompt is its own.
    parts = [
        language_line(language),
        "",
        f"Page title: {title}",
        "",
        "Sanitized summary of the new notes:",
        summary,
    ]
    if existing_web.strip():
        parts += ["", "Current page, in OpenUI Lang (keep what still holds):", existing_web]
    elif existing_md.strip():
        parts += ["", "Current page, in Markdown (keep what still holds):", existing_md]
    return "\n".join(parts)


def write_web(
    web_llm: LLM,
    *,
    title: str,
    summary: str,
    existing_md: str = "",
    existing_web: str = "",
    language: str = FALLBACK_LANGUAGE,
) -> Page:
    """Ask the web agent for the page in OpenUI Lang and derive its Markdown.

    Raises when the call fails or the answer is not a page.
    """
    brief = _brief(
        title=title,
        summary=summary,
        existing_md=existing_md,
        existing_web=existing_web,
        language=language,
    )
    # The Gateway expands its short config block; any other model gets the whole catalogue.
    system = openui.gateway_prompt() if getattr(web_llm, "gateway", False) else openui.full_prompt()
    raw = web_llm.complete_text(system, brief)
    source = openui.strip_fence(raw)
    root = openui.parse(source)

    unknown = openui.unknown_components(root)
    if unknown:
        log.warning("page uses components outside the catalogue: %s", sorted(unknown))

    markdown = openui.to_markdown(root)
    if not markdown:
        raise openui.ParseError("the page has no content")
    return Page(content_md=markdown, content_web=source, source="web", model=_name(web_llm))


def _name(llm: LLM) -> str:
    return getattr(llm, "model", None) or "unknown"


def build_page(
    llm: LLM,
    web_llm: LLM | None,
    *,
    title: str,
    summary: str,
    existing_md: str = "",
    existing_web: str = "",
    language: str = FALLBACK_LANGUAGE,
) -> Page:
    """Write the page, in the class `language`, with the first model that manages it.

    The web model, when there is one, writes it as OpenUI Lang; if it fails, the main model
    `llm` writes the same OpenUI Lang; if that isn't a page either, the notes agent writes
    Markdown alone and `content_web` is left empty. `content_md` is always set, for the RAG.
    """
    reasons: list[str] = []
    web_failed = False
    page_args = dict(
        title=title,
        summary=summary,
        existing_md=existing_md,
        existing_web=existing_web,
        language=language,
    )

    for writer in (web_llm, llm):
        if writer is None:
            continue
        try:
            page = write_web(writer, **page_args)
        except Exception as exc:  # any failure moves on to the next model; the pass goes on
            reasons.append(f"{_name(writer)} failed: {exc}")
            log.warning("%s; trying the next model", reasons[-1])
            web_failed = web_failed or writer is web_llm
            continue
        page.fallback_reason = "; ".join(reasons)
        page.web_failed = web_failed
        return page

    markdown = write_markdown(
        llm, title=title, summary=summary, existing_md=existing_md, language=language
    )
    return Page(
        content_md=markdown.strip(),
        content_web="",
        source="markdown",
        model=_name(llm),
        fallback_reason="; ".join(reasons),
        web_failed=web_failed,
    )
