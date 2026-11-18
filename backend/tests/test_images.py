"""Images for a note, from Wikimedia Commons."""

from __future__ import annotations

from app.agents.images import images_tool, search_commons


class _Response:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class _Client:
    def __init__(self, data):
        self.data = data
        self.params = None

    def get(self, url, params):
        self.params = params
        return _Response(self.data)


COMMONS = {
    "query": {
        "pages": {
            "2": {
                "index": 2,
                "title": "File:B.jpg",
                "imageinfo": [{"thumburl": "https://x/b.jpg?utm_source=y", "descriptionurl": "https://c/B", "extmetadata": {}}],
            },
            "1": {
                "index": 1,
                "title": "File:A &amp; co.jpg",
                "imageinfo": [
                    {
                        "thumburl": "https://x/a.jpg",
                        "descriptionurl": "https://c/A",
                        "extmetadata": {
                            "Artist": {"value": '<a href="u">Ana</a>'},
                            "LicenseShortName": {"value": "CC BY-SA 4.0"},
                        },
                    }
                ],
            },
        }
    }
}


def test_commons_results_come_in_order_with_their_credit():
    client = _Client(COMMONS)
    found = search_commons("raspberry pi", client=client)
    assert client.params["gsrsearch"] == "raspberry pi filetype:bitmap"
    assert found[0] == {"title": "A & co.jpg", "url": "https://x/a.jpg", "page": "https://c/A", "author": "Ana", "license": "CC BY-SA 4.0"}
    assert found[1]["url"] == "https://x/b.jpg" and found[1]["author"] == "unknown"


def test_a_failed_search_is_no_image():
    class Broken:
        def get(self, *a, **k):
            raise OSError("down")

    assert search_commons("x", client=Broken()) == []
    assert "No image" in images_tool(lambda q: [])("search_images", {"query": "x"})


def test_the_tool_lists_url_page_author_and_license():
    run = images_tool(lambda q: [{"title": "A", "url": "u", "page": "p", "author": "Ana", "license": "CC0"}])
    text = run("search_images", {"query": "x"})
    assert "url: u" in text and "page: p" in text and "author: Ana" in text and "license: CC0" in text
    assert "needs a query" in run("search_images", {})
