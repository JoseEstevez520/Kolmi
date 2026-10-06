from __future__ import annotations

from dataclasses import dataclass

from markdown_it import MarkdownIt

# A section past this many characters is cut in parts, between its top-level blocks: a part small
# enough that its embedding is about one thing, big enough to be read on its own.
MAX_CHARS = 1500
SEPARATOR = " › "

# CommonMark with GFM tables, so a table is one block, as a fenced code block is.
_md = MarkdownIt("commonmark").enable("table")


@dataclass
class Chunk:
    heading: str  # the headings it sits under, "H1 › H2 › H3"; empty before the first one
    content: str  # the section's Markdown as written, without its heading line


def _sections(md: str) -> list[tuple[str, list[tuple[int, int]]]]:
    """The page as (breadcrumb, its top-level blocks as line ranges), one per heading."""
    trail: list[tuple[int, str]] = []
    sections: list[tuple[str, list[tuple[int, int]]]] = [("", [])]
    tokens = _md.parse(md)
    for i, token in enumerate(tokens):
        # A top-level block starts with a level-0 token that opens it or stands alone.
        if token.level != 0 or token.nesting == -1 or token.map is None:
            continue
        if token.type == "heading_open":
            depth = int(token.tag[1:])
            title = tokens[i + 1].content.strip() if i + 1 < len(tokens) else ""
            trail = [(d, t) for d, t in trail if d < depth] + [(depth, title)]
            sections.append((SEPARATOR.join(t for _, t in trail if t), []))
            continue
        sections[-1][1].append((token.map[0], token.map[1]))
    return sections


def chunk_markdown(md: str) -> list[Chunk]:
    """A page's Markdown cut at its headings (any level), each part under its breadcrumb.

    Fenced code and tables are blocks of their own and are never cut; a section longer than
    MAX_CHARS is split between its top-level blocks, and a single huge block stays whole. Each
    chunk keeps the Markdown as written. Sections with nothing in them are dropped.
    """
    lines = md.splitlines()

    def text(start: int, end: int) -> str:
        return "\n".join(lines[start:end]).strip()

    chunks: list[Chunk] = []
    for heading, blocks in _sections(md):
        group: list[tuple[int, int]] = []
        for block in blocks:
            if group and len(text(group[0][0], block[1])) > MAX_CHARS:
                chunks.append(Chunk(heading, text(group[0][0], group[-1][1])))
                group = []
            group.append(block)
        if group:
            chunks.append(Chunk(heading, text(group[0][0], group[-1][1])))
    return [chunk for chunk in chunks if chunk.content]
