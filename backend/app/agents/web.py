from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from ..class_settings import FALLBACK_LANGUAGE
from . import openui
from .client import LLM
from .prompts import language_line, tree_lines, visual_system

log = logging.getLogger(__name__)


@dataclass
class Page:
    """A page's web (`content_web`), and how it was made. Its Markdown is the notes agent's."""

    content_web: str
    # "web" when it was written now; "kept" when no model managed it and the page keeps its
    # previous web; "markdown" when there was none, so the page shows its Markdown.
    source: str
    # The model that wrote it.
    model: str = ""
    # Why the web model was not the one that wrote it, when it wasn't.
    fallback_reason: str = ""
    # Whether the web model was tried and failed, so the pass can stop asking it.
    web_failed: bool = False
    # Each Diagram or Artifact the page asked for: drawn, or dropped and why.
    visuals: list[dict[str, Any]] = field(default_factory=list)


def _brief(*, title: str, markdown: str, existing_web: str, language: str, index: str = "") -> str:
    # The language goes in the brief: through the Gateway the system prompt is its own.
    parts = [
        language_line(language),
        "",
        f"Page title: {title}",
        "",
        "The page's notes, in Markdown (the page says all of this, and nothing more):",
        markdown,
    ]
    if existing_web.strip():
        parts += ["", "Current page, in OpenUI Lang (keep what still holds):", existing_web]
    parts += tree_lines(index)
    return "\n".join(parts)


def write_web(
    web_llm: LLM,
    *,
    title: str,
    markdown: str,
    existing_web: str = "",
    language: str = FALLBACK_LANGUAGE,
    index: str = "",
) -> Page:
    """Ask a model to turn the page's notes (`markdown`) into the page in OpenUI Lang.

    Raises when the call fails or the answer is not a page.
    """
    brief = _brief(
        title=title, markdown=markdown, existing_web=existing_web, language=language, index=index
    )
    # The Gateway expands its short config block; any other model gets the whole catalogue.
    system = openui.gateway_prompt() if getattr(web_llm, "gateway", False) else openui.full_prompt()
    raw = web_llm.complete_text(system, brief)
    source = openui.strip_fence(raw)
    root = openui.parse(source)

    unknown = openui.unknown_components(root)
    if unknown:
        log.warning("page uses components outside the catalogue: %s", sorted(unknown))

    blocks = root.args[0] if root.args and isinstance(root.args[0], list) else []
    if not any(isinstance(block, openui.Node) for block in blocks):
        raise openui.ParseError("the page has no content")
    return Page(content_web=source, source="web", model=_name(web_llm))


def _name(llm: LLM) -> str:
    return getattr(llm, "model", None) or "unknown"


# -- the visuals: a page's Diagram and Artifact briefs, drawn by the main model ----------------

# For each kind: the argument with the brief, the one the drawing goes in, and what it is.
_VISUALS = {"Diagram": (1, 3, "svg"), "Artifact": (1, 3, "piece")}
_DROP = object()
_SVG = re.compile(r"<svg\b.*</svg>", re.S | re.I)
# A piece: from its <template> to the last closing tag of the component.
_PIECE = re.compile(r"<template\b.*</(?:template|script|style)>", re.S | re.I)
_OUTSIDE = re.compile(r"""(?:src|href)\s*=\s*["']?\s*(?:https?:)?//""", re.I)
# What a piece may import, as the sandbox runtime reads it: named imports from these two only.
_IMPORTABLE = {"vue", "@joseestevez/vue-elastic-ui"}
_NAMED_IMPORT = re.compile(r"""^\s*import\s*\{[^}]*\}\s*from\s*['"]([^'"]+)['"]""", re.M)
_ANY_IMPORT = re.compile(r"^\s*import\b.*$", re.M)


def _piece_problem(piece: str) -> str:
    """What stops a piece running on the sandbox runtime, or "" when nothing does."""
    if not re.search(r"<template(\s[^>]*)?>", piece, re.I):
        return "there is no <template>"
    script = re.search(r"<script(\s[^>]*)?>(.*?)</script>", piece, re.S | re.I)
    if not script:
        return "there is no <script> with export default { setup() { ... } }"
    if re.search(r"\bsetup\b", script.group(1) or ""):
        return (
            "<script setup> cannot run in the frame: write a plain <script> with "
            "export default { setup() { ... return { ... } } }"
        )
    body = script.group(2)
    if not re.search(r"\bexport\s+default\b", body):
        return "the <script> has no export default"
    for line in _ANY_IMPORT.findall(body):
        named = _NAMED_IMPORT.match(line)
        if not named:
            return f"only named imports work ({line.strip()})"
        if named.group(1) not in _IMPORTABLE:
            return f'it imports from "{named.group(1)}": only vue and @joseestevez/vue-elastic-ui'
    return ""


def _problem(kind: str, answer: str) -> tuple[str, str]:
    """The usable drawing in `answer` and, when there is none, what is wrong with it."""
    text = openui.strip_fence(answer)
    match = (_SVG if kind == "svg" else _PIECE).search(text)
    if not match:
        if kind == "svg":
            return "", "there is no complete <svg> element"
        return "", "there is no <template> followed by a <script>"
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
    else:
        problem = _piece_problem(drawing)
        if problem:
            return "", problem
    if _OUTSIDE.search(drawing):
        return "", "it loads something from outside (a src or href to another site)"
    # Usable, but worth one more try.
    return drawing, _overlap(drawing) if kind == "svg" else ""


def page_problems(source: str) -> list[str]:
    """What stops `source` from being saved as a page's web as it is, with no web agent behind
    it: the catalogue's checks (`openui.problems`), then each Diagram's and Artifact's drawing,
    which must be there and pass the same checks a drawn one does (the renderer draws nothing
    for a brief alone). Empty when the page holds up."""
    found = openui.problems(source)
    if found:
        return found

    def visit(value: Any) -> None:
        if isinstance(value, openui.Node):
            if value.name in _VISUALS:
                brief_at, drawn_at, kind = _VISUALS[value.name]
                args = list(value.args) + [None] * (drawn_at + 1 - len(value.args))
                label = str(args[0] or "")
                slot = "svg" if kind == "svg" else "piece"
                drawing = args[drawn_at] if isinstance(args[drawn_at], str) else ""
                if not drawing.strip():
                    found.append(
                        f"The {value.name} {label!r} has no drawing: put it in its {slot} argument "
                        f"(the {drawn_at + 1}th), or leave the {value.name} out. A brief alone shows nothing."
                    )
                else:
                    usable, problem = _problem(kind, drawing)
                    if not usable:
                        found.append(f"The {value.name} {label!r}, in its {slot}: {problem}.")
            for arg in value.args:
                visit(arg)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for _, expr in openui.statements(source):
        visit(expr)
    return found[: openui.MAX_PROBLEMS]


# The font sizes the theme gives its text classes (frontend theme.js); CSS wins over a
# font-size attribute, a style attribute over both.
_CLASS_SIZES = {"diagram-label": 13.0, "diagram-text": 12.0}
_TRANSLATE = re.compile(r"\s*translate\(\s*(-?[\d.]+)(?:[\s,]+(-?[\d.]+))?\s*\)\s*")
_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _number(value: str | None) -> float | None:
    match = _NUM.match((value or "").strip())
    return float(match.group(0)) if match else None


def _style(element: ET.Element, name: str) -> str | None:
    match = re.search(rf"(?:^|;)\s*{name}\s*:\s*([^;]+)", element.get("style") or "")
    return match.group(1).strip() if match else None


def _overlap(svg: str) -> str:
    """Two labels drawn over each other, by a rough measure of each text's box.

    Only what it can measure counts: a <text> with plain x and y, under translate() at most.
    Returns "" when it finds none, or cannot tell.
    """
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return ""
    boxes: list[tuple[str, float, float, float, float]] = []

    def walk(element: ET.Element, dx: float, dy: float, size: float, anchor: str) -> None:
        transform = element.get("transform")
        if transform:
            move = _TRANSLATE.fullmatch(transform)
            if not move:  # rotated or scaled: out of this rough measure
                return
            dx, dy = dx + float(move.group(1)), dy + float(move.group(2) or 0)
        classes = (element.get("class") or "").split()
        size = (
            _number(_style(element, "font-size"))
            or next((_CLASS_SIZES[c] for c in classes if c in _CLASS_SIZES), None)
            or _number(element.get("font-size"))
            or size
        )
        anchor = _style(element, "text-anchor") or element.get("text-anchor") or anchor
        if element.tag.rsplit("}", 1)[-1] == "text":
            text = " ".join("".join(element.itertext()).split())
            x, y = _number(element.get("x")), _number(element.get("y"))
            placed = any(child.get("x") or child.get("y") or child.get("dy") for child in element)
            if text and x is not None and y is not None and not placed:
                width = 0.58 * size * len(text)
                left = dx + x - {"middle": width / 2, "end": width}.get(anchor, 0)
                top = dy + y - 0.8 * size
                boxes.append((text, left, top, left + width, top + size))
            return
        for child in element:
            walk(child, dx, dy, size, anchor)

    walk(root, 0.0, 0.0, 16.0, "start")
    for i, (a, al, at, ar, ab) in enumerate(boxes):
        for b, bl, bt, br, bb in boxes[i + 1 :]:
            if min(ar, br) - max(al, bl) > 2 and min(ab, bb) - max(at, bt) > 2:
                return (
                    f'the labels "{a}" and "{b}" overlap: move one so each has its own space'
                )
    return ""


def _draw(
    llm: LLM, kind: str, brief: str, label: str, notes: str, language: str
) -> tuple[str, str]:
    """One drawing from its brief, with one retry; returns it, or "" and why not.

    A drawing whose only problem is overlapping labels is sent back too, but kept if the second
    answer is no better: a chart with two labels too close beats no chart.
    """
    system = visual_system(kind, language)
    request = f"What it shows, in one line: {label}\n\nBrief:\n{brief}"
    if notes.strip():
        request += f"\n\nThe page's notes, in Markdown (the data it may use):\n{notes}"
    problem = ""
    usable = ""
    for attempt in range(2):
        try:
            answer = llm.complete_text(system, request)
        except Exception as exc:  # one retry, then the block is dropped
            problem = f"the call failed: {exc}"
            continue
        drawing, problem = _problem(kind, answer)
        if drawing and not problem:
            return drawing, ""
        usable = drawing or usable
        if attempt == 0:
            request = (
                f"{request}\n\nYour previous answer:\n{answer}\n\nIt cannot be used: {problem}. "
                "Answer again with the fixed version only."
            )
    return usable, problem

def draw_visuals(
    llm: LLM, source: str, *, language: str, notes: str = ""
) -> tuple[str, list[dict[str, Any]]]:
    """Draw the page's Diagram and Artifact briefs with `llm` and write them into the source.

    `notes`, the page's Markdown, goes with each brief: the data a drawing may use.

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
                drawing, problem = _draw(llm, kind, brief, label, notes, language)
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
    markdown: str,
    existing_web: str = "",
    language: str = FALLBACK_LANGUAGE,
    index: str = "",
) -> Page:
    """Turn the page's notes (`markdown`) into its web, in the class `language`.

    The web model, when there is one, writes it as OpenUI Lang; if it fails, the main model
    `llm` writes the same OpenUI Lang; `index` is the tree's, for links to other pages. Then the main model draws the page's Diagram and Artifact
    briefs (`draw_visuals`), with the notes as context. If neither writes a page, the page keeps
    `existing_web` (empty for a new page, which then shows its Markdown).
    """
    reasons: list[str] = [] if markdown.strip() else ["there are no notes to write it from"]
    web_failed = False

    for writer in (web_llm, llm) if markdown.strip() else ():
        if writer is None:
            continue
        try:
            page = write_web(
                writer,
                title=title,
                markdown=markdown,
                existing_web=existing_web,
                language=language,
                index=index,
            )
        except Exception as exc:  # any failure moves on to the next model; the pass goes on
            reasons.append(f"{_name(writer)} failed: {exc}")
            log.warning("%s; trying the next model", reasons[-1])
            web_failed = web_failed or writer is web_llm
            continue
        page.fallback_reason = "; ".join(reasons)
        page.web_failed = web_failed
        # The figures and pieces it asked for, drawn by the main model; never fails the page.
        try:
            page.content_web, page.visuals = draw_visuals(
                llm, page.content_web, notes=markdown, language=language
            )
        except Exception as exc:
            log.warning("could not draw the page's visuals: %s", exc)
        return page

    return Page(
        content_web=existing_web,
        source="kept" if existing_web.strip() else "markdown",
        model="",
        fallback_reason="; ".join(reasons),
        web_failed=web_failed,
    )
