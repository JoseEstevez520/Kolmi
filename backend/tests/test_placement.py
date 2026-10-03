from __future__ import annotations

import pytest

from app.agents.schemas import Batch, NewPage
from app.passes.daily import _resolve_target
from tests.fakes import FakeStore


def _store() -> FakeStore:
    nodes = [{"id": 10, "parent_id": None, "kind": "section", "position": 0}]
    nodes += [
        {"id": 20 + i, "parent_id": 10, "kind": "page", "position": i} for i in range(3)
    ]
    # A page elsewhere, which must not move.
    nodes.append({"id": 99, "parent_id": None, "kind": "page", "position": 1})
    return FakeStore(nodes=nodes)


def _order(store: FakeStore, new_id: int) -> list[int]:
    kids = [n for n in store.nodes() if n["parent_id"] == 10]
    assert sorted(n["position"] for n in kids) == list(range(len(kids)))
    return [n["id"] for n in sorted(kids, key=lambda n: n["position"])]


@pytest.mark.parametrize(
    ("placement", "after", "expected"),
    [
        ("after", 20, [20, 100, 21, 22]),
        ("after", 22, [20, 21, 22, 100]),
        ("first", None, [100, 20, 21, 22]),
        ("last", None, [20, 21, 22, 100]),
        ("after", 555, [20, 21, 22, 100]),  # unknown id: the end
        ("after", None, [20, 21, 22, 100]),
    ],
)
def test_new_page_placement(placement, after, expected):
    store = _store()
    store._next_id = 100
    page = store.create_page(
        parent_id=10, title="New", description="", placement=placement, after_node_id=after
    )
    assert _order(store, page["id"]) == expected
    assert next(n for n in store.nodes() if n["id"] == 99)["position"] == 1


def test_placement_reason_reaches_the_log():
    store = _store()
    batch = Batch(
        note_ids=[],
        action="create",
        summary="s",
        reason="new topic",
        new_page=NewPage(
            parent_id=10,
            title="Basics",
            placement="first",
            placement_reason="the others build on it",
        ),
    )
    page = _resolve_target(store, 1, batch, {"created": 0, "flagged": []})
    assert store.logs[0]["reason"] == "new topic the others build on it"
    assert _order(store, page["id"])[0] == page["id"]
