"""The page catalogue as an AI over the MCP reads it: the components with their parameters and
allowed values, when to use each, examples, and how to write a Diagram's svg and an Artifact's
piece itself. Built from the web agent's own prompt (`openui/page.txt`, generated from the
frontend's catalogue), so the two never disagree; only what is the agent's alone is changed.
"""

from __future__ import annotations

import re

from . import openui
from .prompts import drawing_guide

URI = "kolmi://catalogue"
TITLE = "The page catalogue"

_HEADER = """\
# The page catalogue

What `write_page_web` accepts: a page in OpenUI Lang, built from the components below. The
sections that follow say what each component takes (with its allowed values), when to use it, and
show examples. Unlike the web agent, you write the whole page: the text, and also each Diagram's
`svg` and each Artifact's `piece`. Both are rules of their own at the end of this guide, and the
page is checked before it is saved, with each problem listed by line.

The page's words go in the class language: {language}.

"""

_TAIL = "\n\n## Writing the drawings yourself\n\n"

# The web agent writes a brief and a drawing model draws it; over the MCP there is no drawing model.
_BRIEF = re.compile(r"Write a brief, not the (?:drawing|code):.*?Leave `(?:svg|piece)` out\.")
_BRIEFS = {
    "Diagram": "Write the SVG yourself in `svg` (see \"Writing the drawings yourself\"); the `brief` says what it shows.",
    "Artifact": "Write the Vue component yourself in `piece` (see \"Writing the drawings yourself\"); the `brief` says what it is for.",
}


def catalogue_guide(language: str) -> str:
    """The guide for the class `language`."""
    full = openui.full_prompt()
    body = full[full.index("# Web notes") : full.index("## Important Rules")]
    # The streaming notes are for the web agent's output; a page sent whole has no use for them.
    start = body.index("## Hoisting & Streaming")
    body = body[:start] + body[body.index("## Examples") :]
    lines = []
    for line in body.splitlines():
        for name, text in _BRIEFS.items():
            if line.startswith(f"{name}("):
                line = _BRIEF.sub(text, line)
        lines.append(line)
    return _HEADER.replace("{language}", language) + "\n".join(lines).rstrip() + _TAIL + drawing_guide(language)
