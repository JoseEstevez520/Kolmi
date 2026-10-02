from __future__ import annotations


def build_page(markdown: str) -> tuple[str, str]:
    """Turn the notes agent's Markdown into the page fields.

    For now the source is Markdown and there is no OpenUI Lang yet, so
    `content_web` stays empty. When the page format lands, this is where the
    web agent calls Thesys and fills it in.
    """
    return markdown.strip(), ""
