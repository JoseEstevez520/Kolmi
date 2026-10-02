from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from ..class_settings import FALLBACK_LANGUAGE
from . import openui
from .client import LLM
from .notes import write_markdown
from .prompts import language_line, visual_system

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
    # Each Diagram or Artifact the page asked for: drawn, or dropped and why.
    visuals: list[dict[str, Any]] = field(default_factory=list)


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


# -- the visuals: a page's Diagram and Artifact briefs, drawn by the main model ----------------

# For each kind: the argument with the brief, the one the drawing goes in, and what it is.
_VISUALS = {"Diagram": (1, 3, "svg"), "Artifact": (1, 3, "html")}
_DROP = object()
_SVG = re.compile(r"<svg\b.*</svg>", re.S | re.I)
_HTML = re.compile(r"<!doctype html.*</html>|<html\b.*</html>", re.S | re.I)
_OUTSIDE = re.compile(r"""(?:src|href)\s*=\s*["']?\s*(?:https?:)?//""", re.I)


def _problem(kind: str, answer: str) -> tuple[str, str]:
    """The usable drawing in `answer` and, when there is none, what is wrong with it."""
    text = openui.strip_fence(answer)
    match = (_SVG if kind == "svg" else _HTML).search(text)
    if not match:
        if kind == "svg":
            return "", "there is no complete <svg> element"
        return "", "the HTML document is incomplete: it must run from <!doctype html> to </html>"
    drawing = match.group(0)
    if kind == "svg":
        opening = re.match(r"<svg\b[^>]*>", drawing, re.I)
        if not opening or "viewbox" not in opening.group(0).lower():
            return "", "the <svg> has no viewBox"
        if re.search(r"<script\b", drawing, re.I):
            return "", "it contains a <script>"
        if re.search(r"\son[a-z]+\s*=", drawing, re.I):
            return "", "it has an event attribute (onclick, onload...)"
        if re.search(r"<foreignObject\b", drawing, re.I):
            return "", "it contains a <foreignObject>"
    if _OUTSIDE.search(drawing):
        return "", "it loads something from outside (a src or href to another site)"
    return drawing, ""


def _draw(llm: LLM, kind: str, brief: str, label: str, language: str) -> tuple[str, str]:
    """One drawing from its brief, with one retry; returns it, or "" and why not."""
    system = visual_system(kind, language)
    request = f"What it shows, in one line: {label}\n\nBrief:\n{brief}"
    problem = ""
    for attempt in range(2):
        try:
            answer = llm.complete_text(system, request)
        except Exception as exc:  # one retry, then the block is dropped
            problem = f"the call failed: {exc}"
            continue
        drawing, problem = _problem(kind, answer)
        if drawing:
            return drawing, ""
        if attempt == 0:
            request = (
                f"{request}\n\nYour previous answer:\n{answer}\n\nIt cannot be used: {problem}. "
                "Answer again with the fixed version only."
            )
    return "", problem


def draw_visuals(llm: LLM, source: str, *, language: str) -> tuple[str, list[dict[str, Any]]]:
    """Draw the page's Diagram and Artifact briefs with `llm` and write them into the source.

    A block whose drawing fails twice is taken out of the page; the report says why. A block
    already drawn (the current page's, kept on an update) is left as it is.
    """
    report: list[dict[str, Any]] = []
    dropped: set[str] = set()

    def visit(value: Any) -> Any:
        if isinstance(value, openui.Node):
            if value.name in _VISUALS:
                brief_at, drawn_at, kind = _VISUALS[value.name]
                args = list(value.args) + [None] * (drawn_at + 1 - len(value.args))
                brief, label = str(args[brief_at] or ""), str(args[0] or "")
                if args[drawn_at] or brief.lstrip().startswith("<"):
                    return value
                drawing, problem = _draw(llm, kind, brief, label, language)
                report.append(
                    {"kind": value.name, "label": label, "drawn": bool(drawing), "reason": problem}
                )
                if not drawing:
                    log.warning("%s %r dropped: %s", value.name, label, problem)
                    return _DROP
                args[drawn_at] = drawing
                return openui.Node(value.name, args)
            return openui.Node(value.name, [visit(arg) for arg in value.args])
        if isinstance(value, list):
            return [item for item in map(visit, value) if item is not _DROP]
        return value

    kept = []
    for name, expr in openui.statements(source):
        value = visit(expr)
        if value is _DROP:
            dropped.add(name)
        else:
            kept.append((name, value))
    if not report:
        return source, []

    def prune(value: Any) -> Any:
        if isinstance(value, openui.Node):
            return openui.Node(value.name, [prune(arg) for arg in value.args])
        if isinstance(value, list):
            return [
                prune(item)
                for item in value
                if not (isinstance(item, openui.Ref) and item.name in dropped)
            ]
        return value

    return openui.dump([(name, prune(expr)) for name, expr in kept]), report


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
    The main model also draws the page's Diagram and Artifact briefs (`draw_visuals`).
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
        # The figures and pieces it asked for, drawn by the main model; never fails the page.
        try:
            source, page.visuals = draw_visuals(llm, page.content_web, language=language)
            if page.visuals:
                page.content_web = source
                page.content_md = openui.to_markdown(openui.parse(source))
        except Exception as exc:
            log.warning("could not draw the page's visuals: %s", exc)
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
