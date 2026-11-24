"""The pieces the AI writes into a note, checked as the pass checks a page's, and mended once.

What the AI in a note writes is Markdown with pieces in ```kolmi-ai fences, each an OpenUI Lang
program with an `Answer` root. A piece that doesn't parse would show as code in the note, so each
one goes through the same checks a page does (`openui.problems`; the chat's parts have the same
signatures as the page's), and one with problems goes back to the model once with them, as
`draw_visuals` does for a page's drawings. One still broken is dropped: the note keeps its text.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from . import openui
from .client import LLM
from .web import draw_visuals

log = logging.getLogger(__name__)

FENCE = re.compile(r"```kolmi-ai[^\n]*\n(.*?)```", re.S)
_ROOT = re.compile(r"^(\s*root\s*=\s*)Answer\(", re.M)

_MEND = """\
You fix one piece of a student's note: an OpenUI Lang program that doesn't parse. Keep what it \
shows; change only what the problems point at. Answer with the program alone, no fence, no prose.

Its syntax: the first line is `root = Answer([...])`; then one statement per line, \
`name = Component(args)`; arguments positional, in the signature's order, never `name: value` or \
`name = value` inside a call; a component is never written inside another's arguments (it gets \
its own line and its name goes in the list); strings double-quoted.

Parts:
{parts}
"""


def piece_problems(program: str) -> list[str]:
    """What stops a piece (`root = Answer([...])`) from being drawn; empty when it holds up. Checked
    as a page, whose blocks have the same signatures."""
    as_page = _ROOT.sub(r"\1Page(", program.strip(), count=1)
    return [p.replace("Page(", "Answer(") for p in openui.problems(as_page)]


@dataclass
class Mend:
    index: int  # which ```kolmi-ai fence of the answer, from 0
    program: str | None  # the mended program, or None to drop the piece


def mend_pieces(
    llm: LLM, answer: str, parts: str, *, language: str = "en", notes: str = ""
) -> list[Mend]:
    """For each piece of `answer` that doesn't hold up, the model's fix (asked once, with the
    problems), or None when the fix doesn't hold up either."""
    mends: list[Mend] = []
    for index, match in enumerate(FENCE.finditer(answer)):
        program = match.group(1).strip()
        found = piece_problems(program)
        fixed: str | None = program if not found else None
        try:
            if found:
                reply = llm.complete_text(
                    _MEND.replace("{parts}", parts),
                    "Problems:\n" + "\n".join(f"- {p}" for p in found) + f"\n\nThe piece:\n{program}",
                )
                candidate = openui.strip_fence(reply).strip()
                if candidate and not piece_problems(candidate):
                    fixed = candidate
            if fixed is not None:
                fixed, _ = draw_visuals(llm, fixed, language=language, notes=notes)
        except Exception as exc:  # a failed call drops the piece, never the answer
            log.warning("couldn't mend a note's piece: %s", exc)
            fixed = None
        if fixed != program:
            mends.append(Mend(index, fixed))
    return mends


def apply_mends(answer: str, mends: list[Mend]) -> str:
    """`answer` with each mended piece put in, and each dropped one taken out."""
    by_index = {m.index: m for m in mends}
    count = -1

    def swap(match: re.Match) -> str:
        nonlocal count
        count += 1
        mend = by_index.get(count)
        if mend is None:
            return match.group(0)
        return "" if mend.program is None else f"```kolmi-ai\n{mend.program}\n```"

    return FENCE.sub(swap, answer)
