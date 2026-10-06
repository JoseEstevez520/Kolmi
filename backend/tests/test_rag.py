from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import pytest

from app.agents.chat import run_chat
from app.config import get_settings
from app.rag.chunker import chunk_markdown
from app.rag.embeddings import get_embedder
from app.rag.index import index_page, index_pages, reindex_all, search
from tests.fakes import FakeLLM

DIM = 8


class FakeEmbedder:
    """Fixed-size vectors, one per text; counts the calls and keeps every text it was handed."""

    def __init__(self, fail: bool = False) -> None:
        self.calls = 0
        self.texts: list[str] = []
        self.fail = fail

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        self.texts += list(texts)
        if self.fail:
            raise RuntimeError("embeddings down")
        return [[float(len(t) % 7)] * DIM for t in texts]


class _Response:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _Query:
    """One chained call on a fake table: select, insert, update or delete, then filters."""

    def __init__(self, table: _Table, op: str, data: Any = None) -> None:
        self.table = table
        self.op = op
        self.data = data
        self.filters: list[Any] = []

    def eq(self, column: str, value: Any) -> _Query:
        self.filters.append(lambda r: r.get(column) == value)
        return self

    def neq(self, column: str, value: Any) -> _Query:
        self.filters.append(lambda r: r.get(column) != value)
        return self

    def in_(self, column: str, values: list[Any]) -> _Query:
        values = list(values)
        self.filters.append(lambda r: r.get(column) in values)
        return self

    def order(self, *_args: Any, **_kwargs: Any) -> _Query:
        return self

    def limit(self, _n: int) -> _Query:
        return self

    def range(self, *_args: Any) -> _Query:
        return self

    def _matches(self) -> list[dict[str, Any]]:
        return [r for r in self.table.rows if all(f(r) for f in self.filters)]

    def execute(self) -> _Response:
        if self.op == "insert":
            rows = self.data if isinstance(self.data, list) else [self.data]
            stored = []
            for row in rows:
                self.table.next_id += 1
                stored.append({"id": self.table.next_id, **row})
            self.table.rows += stored
            return _Response([dict(r) for r in stored])
        found = self._matches()
        if self.op == "delete":
            self.table.rows = [r for r in self.table.rows if r not in found]
        elif self.op == "update":
            for row in found:
                row.update(self.data)
        return _Response([dict(r) for r in found])


class _Table:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = [dict(r) for r in (rows or [])]
        self.next_id = 1000

    def select(self, *_args: Any, **_kwargs: Any) -> _Query:
        return _Query(self, "select")

    def insert(self, data: Any) -> _Query:
        return _Query(self, "insert", data)

    def update(self, data: dict[str, Any]) -> _Query:
        return _Query(self, "update", data)

    def delete(self) -> _Query:
        return _Query(self, "delete")


class _Rpc:
    def __init__(self, client: _Client, name: str, params: dict[str, Any]) -> None:
        self.client = client
        client.rpc_calls.append((name, params))

    def execute(self) -> _Response:
        if self.client.rpc_error:
            raise self.client.rpc_error
        return _Response([dict(r) for r in self.client.rpc_rows])


class _Client:
    """Just enough of the Supabase client for `nodes`, `page_chunks` and one rpc."""

    def __init__(self, nodes: list[dict[str, Any]] | None = None) -> None:
        self.tables = {"nodes": _Table(nodes), "page_chunks": _Table()}
        self.rpc_calls: list[tuple[str, dict[str, Any]]] = []
        self.rpc_rows: list[dict[str, Any]] = []
        self.rpc_error: Exception | None = None

    def table(self, name: str) -> _Table:
        assert name in self.tables, name
        return self.tables[name]

    def rpc(self, name: str, params: dict[str, Any]) -> _Rpc:
        return _Rpc(self, name, params)

    def chunks(self, node_id: int | None = None) -> list[dict[str, Any]]:
        rows = self.tables["page_chunks"].rows
        return [r for r in rows if node_id is None or r["node_id"] == node_id]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _page(node_id: int, content_md: str) -> dict[str, Any]:
    return {
        "id": node_id,
        "parent_id": None,
        "kind": "page",
        "title": f"Page {node_id}",
        "position": node_id,
        "content_md": content_md,
    }


GIT = "# Git\n\nVersion control.\n\n## Amend\n\nUse `git commit --amend`.\n"
SQL = "# SQL\n\n## Joins\n\nInner joins keep matching rows.\n"


@pytest.fixture
def no_embedding_key(monkeypatch):
    monkeypatch.setenv("EMBEDDING_API_KEY", "")
    get_settings.cache_clear()
    get_embedder.cache_clear()
    yield
    get_settings.cache_clear()
    get_embedder.cache_clear()


# 1. Chunking


def test_headings_become_breadcrumbs():
    md = (
        "# Git\n\nIntro text.\n\n## Amend\n\nAmend text.\n\n### Deep\n\nDeep text.\n\n"
        "## Stash\n\nStash text.\n"
    )
    chunks = chunk_markdown(md)

    assert [c.heading for c in chunks] == ["Git", "Git › Amend", "Git › Amend › Deep", "Git › Stash"]
    assert "Amend text." in chunks[1].content
    assert "Deep text." not in chunks[1].content
    assert "Stash text." in chunks[3].content


def test_a_code_block_with_hash_lines_stays_whole():
    fence = "```bash\n# not a heading\necho hi\n## nor this\n```"
    md = f"# Shell\n\nBefore.\n\n{fence}\n\nAfter.\n"
    chunks = chunk_markdown(md)

    assert [c.heading for c in chunks] == ["Shell"]
    assert fence in chunks[0].content


def test_a_long_code_block_is_never_split():
    fence = "```python\n" + "\n".join(f"# step {i}\nx = {i}" for i in range(200)) + "\n```"
    assert len(fence) > 1500
    md = f"# Code\n\nIntro paragraph.\n\n{fence}\n\nOutro paragraph.\n"
    chunks = chunk_markdown(md)

    assert sum(fence in c.content for c in chunks) == 1
    assert all(c.heading == "Code" for c in chunks)


def test_a_table_stays_whole():
    rows = "\n".join(f"| cmd{i} | does thing number {i} with some words |" for i in range(60))
    table = f"| Command | What |\n| --- | --- |\n{rows}"
    assert len(table) > 1500
    md = f"# Commands\n\nIntro.\n\n{table}\n\nOutro.\n"
    chunks = chunk_markdown(md)

    assert sum(table in c.content for c in chunks) == 1


def test_a_long_section_splits_between_blocks():
    paragraphs = [f"Paragraph {i}. " + ("word " * 80).strip() for i in range(8)]
    md = "# Long\n\n" + "\n\n".join(paragraphs) + "\n"
    chunks = chunk_markdown(md)

    assert len(chunks) > 1
    assert all(c.heading == "Long" for c in chunks)
    for paragraph in paragraphs:
        assert sum(paragraph in c.content for c in chunks) == 1


def test_no_empty_chunks():
    md = "# Empty\n\n## Also empty\n\n## Full\n\nSomething.\n\n## Trailing\n\n   \n"
    chunks = chunk_markdown(md)

    assert [c.heading for c in chunks] == ["Empty › Full"]
    assert all(c.content.strip() for c in chunks)
    assert chunk_markdown("") == []


# 2. Reindex only what changed


def test_same_content_twice_is_a_no_op():
    client = _Client()
    embedder = FakeEmbedder()

    assert index_page(client, 20, GIT, embedder) is True
    calls, rows = embedder.calls, [dict(r) for r in client.chunks(20)]
    assert calls >= 1
    assert rows

    assert index_page(client, 20, GIT, embedder) is False
    assert embedder.calls == calls
    assert client.chunks(20) == rows


def test_rows_carry_what_a_search_needs():
    client = _Client()
    index_page(client, 20, GIT, FakeEmbedder())

    rows = sorted(client.chunks(20), key=lambda r: r["position"])
    assert [r["heading"] for r in rows] == ["Git", "Git › Amend"]
    assert [r["position"] for r in rows] == list(range(len(rows)))
    assert all(r["content_hash"] == _sha(GIT) for r in rows)
    assert all(len(r["embedding"]) == DIM for r in rows)
    assert "git commit --amend" in rows[1]["content"]


def test_changed_content_replaces_the_rows():
    client = _Client()
    embedder = FakeEmbedder()
    index_page(client, 20, GIT, embedder)
    index_page(client, 31, SQL, embedder)
    other = [dict(r) for r in client.chunks(31)]

    changed = "# Git\n\n## Rebase\n\nRewrite history with `git rebase -i`.\n"
    assert index_page(client, 20, changed, embedder) is True

    rows = client.chunks(20)
    assert [r["heading"] for r in rows] == ["Git › Rebase"]
    assert all(r["content_hash"] == _sha(changed) for r in rows)
    assert client.chunks(31) == other


# 3. index_pages / reindex_all


def test_index_pages_skips_unchanged_pages():
    client = _Client([_page(20, GIT), _page(31, SQL)])
    embedder = FakeEmbedder()
    index_pages(client, [20, 31], embedder)
    assert {r["node_id"] for r in client.chunks()} == {20, 31}

    changed = "# SQL\n\n## Indexes\n\nB-trees make lookups fast.\n"
    client.tables["nodes"].rows[1]["content_md"] = changed
    embedder.texts = []
    index_pages(client, [20, 31], embedder)

    assert embedder.texts
    assert not any("Version control" in t or "amend" in t for t in embedder.texts)
    assert all(r["content_hash"] == _sha(changed) for r in client.chunks(31))
    assert all(r["content_hash"] == _sha(GIT) for r in client.chunks(20))


def test_index_pages_never_raises():
    client = _Client([_page(20, GIT)])
    index_pages(client, [20], FakeEmbedder(fail=True))
    index_pages(client, [999], FakeEmbedder())


def test_reindex_all_skips_unchanged_pages_unless_forced():
    client = _Client([_page(20, GIT), _page(31, SQL)])
    embedder = FakeEmbedder()
    reindex_all(client, embedder)
    assert {r["node_id"] for r in client.chunks()} == {20, 31}

    calls = embedder.calls
    reindex_all(client, embedder)
    assert embedder.calls == calls

    embedder.texts = []
    reindex_all(client, embedder, force=True)
    assert embedder.calls > calls
    assert any("amend" in t for t in embedder.texts)
    assert any("Inner joins" in t for t in embedder.texts)
    assert {r["node_id"] for r in client.chunks()} == {20, 31}


# 4. Empty content


def test_empty_content_deletes_the_rows():
    client = _Client()
    embedder = FakeEmbedder()
    index_page(client, 20, GIT, embedder)
    index_page(client, 31, SQL, embedder)
    calls = embedder.calls

    index_page(client, 20, "", embedder)

    assert client.chunks(20) == []
    assert client.chunks(31)
    assert embedder.calls == calls


def test_deleting_a_node_cascades_to_its_chunks_in_the_database():
    """No code removes the chunks of a deleted node: the foreign key does it."""
    schema = (Path(__file__).resolve().parents[2] / "supabase" / "schema.sql").read_text()
    table = re.search(r"create table if not exists page_chunks \((.*?)\n\);", schema, re.S)
    assert table, "page_chunks is missing from supabase/schema.sql"
    assert re.search(r"node_id\s+bigint[^,]*references nodes\(id\) on delete cascade", table.group(1))


# 5. No embeddings key


def test_no_key_no_embedder(no_embedding_key):
    assert get_embedder() is None


def test_no_key_index_pages_is_a_no_op(no_embedding_key):
    client = _Client([_page(20, GIT)])
    index_pages(client, [20])
    reindex_all(client)
    assert client.chunks() == []


def test_no_key_search_finds_nothing(no_embedding_key):
    client = _Client()
    client.rpc_rows = [{"node_id": 20, "heading": "Git", "content": "x", "score": 0.5}]
    assert search(client, "amend") == []


NODES = [
    {"id": 10, "parent_id": None, "kind": "section", "title": "Tools", "position": 0},
    {"id": 20, "parent_id": 10, "kind": "page", "title": "Git", "position": 0},
]
ANSWER = {"answer": "Use `git commit --amend`.", "sources": [20]}


def _chat_user(**kwargs: Any) -> str:
    llm = FakeLLM(json_response=ANSWER)
    run_chat(llm, "how do I amend?", NODES, read_page=None, **kwargs)
    return llm.calls[0][2]


def test_no_passages_builds_the_same_prompt_as_before():
    before = _chat_user()
    assert _chat_user(passages=None) == before
    assert _chat_user(passages=[]) == before


def test_passages_go_in_the_user_message():
    passage = {
        "node_id": 20,
        "heading": "Git › Amend",
        "content": "Use `git commit --amend` to fix the last commit.",
        "score": 0.9,
    }
    user = _chat_user(passages=[passage])

    assert "20" in user
    assert "Git › Amend" in user
    assert passage["content"] in user
    assert "Question: how do I amend?" in user


# 6. search


def test_search_maps_the_rpc_rows():
    client = _Client()
    client.rpc_rows = [
        {"node_id": 20, "heading": "Git › Amend", "content": "Use amend.", "score": 0.91},
        {"node_id": 31, "heading": "SQL › Joins", "content": "Inner joins.", "score": 0.42},
    ]
    embedder = FakeEmbedder()
    found = search(client, "fix my last commit", k=3, embedder=embedder)

    assert [
        {k: r[k] for k in ("node_id", "heading", "content", "score")} for r in found
    ] == client.rpc_rows
    (name, params), = client.rpc_calls
    assert name == "match_page_chunks"
    assert params["query_text"] == "fix my last commit"
    assert params["query_embedding"] == embedder.embed(["fix my last commit"])[0]
    assert params["match_count"] == 3


def test_search_on_an_rpc_error_finds_nothing():
    client = _Client()
    client.rpc_error = RuntimeError("function match_page_chunks does not exist")
    assert search(client, "anything", embedder=FakeEmbedder()) == []


def test_search_when_embedding_fails_finds_nothing():
    client = _Client()
    assert search(client, "anything", embedder=FakeEmbedder(fail=True)) == []
