"""Images for a note, from Wikimedia Commons (the media library behind Wikipedia).

The AI in a note may show a real thing with a photo (a device, a place, an organism, a person)
when a picture says it better than a drawing. It finds one with the `search_images` tool, which
asks Commons' public API (no key) for freely licensed images and hands back, for each, the URL of
a sized copy, the page it comes from, its author and its licence: what a note needs to show it
and credit it as Commons asks.
"""

from __future__ import annotations

import html
import logging
import re
from typing import Any, Callable

import httpx

log = logging.getLogger(__name__)

API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia asks automated clients for a descriptive User-Agent.
USER_AGENT = "Kolmi/1.0 (class notes app; https://github.com/JoseEstevez520/Kolmi)"
WIDTH = 800
RESULTS = 5

SEARCH_IMAGES_TOOL = {
    "type": "function",
    "function": {
        "name": "search_images",
        "description": (
            "Find a freely licensed photo or illustration on Wikimedia Commons (Wikipedia's media "
            "library) for a real thing a picture shows better than words or a diagram: a device, "
            "a place, an organism, a person, an object. Search in English, with the thing's name."
        ),
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to find, in English."}},
            "required": ["query"],
        },
    },
}

_TAGS = re.compile(r"<[^>]+>")


def _plain(value: Any) -> str:
    return html.unescape(_TAGS.sub("", str(value or ""))).strip()


def search_commons(query: str, client: httpx.Client | None = None) -> list[dict[str, str]]:
    """Up to a few images for `query`: {title, url, page, author, license}. Empty when nothing is
    found or Commons can't be reached."""
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": RESULTS,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": WIDTH,
    }
    try:
        own = client is None
        client = client or httpx.Client(timeout=8, headers={"User-Agent": USER_AGENT})
        try:
            data = client.get(API, params=params).json()
        finally:
            if own:
                client.close()
    except Exception as exc:  # a failed search never breaks the answer
        log.warning("commons search failed: %s", exc)
        return []
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    found = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        url = (info.get("thumburl") or info.get("url") or "").split("?")[0]
        if not url:
            continue
        found.append(
            {
                "title": _plain(page.get("title", "")).removeprefix("File:"),
                "url": url,
                "page": info.get("descriptionurl", ""),
                "author": _plain((meta.get("Artist") or {}).get("value")) or "unknown",
                "license": _plain((meta.get("LicenseShortName") or {}).get("value")) or "see page",
            }
        )
    return found


def images_tool(search: Callable[[str], list[dict[str, str]]] = search_commons):
    """The `search_images` tool for the model: the images found, as text it can choose from."""

    def run(name: str, args: dict[str, Any]) -> str:
        if name != "search_images":
            return f"There is no tool called {name}."
        query = str(args.get("query") or "").strip()
        if not query:
            return "search_images needs a query."
        found = search(query)
        if not found:
            return "No image found; go on without one."
        return "\n\n".join(
            f"{i + 1}. {img['title']}\n   url: {img['url']}\n   page: {img['page']}\n"
            f"   author: {img['author']}\n   license: {img['license']}"
            for i, img in enumerate(found)
        )

    return run
