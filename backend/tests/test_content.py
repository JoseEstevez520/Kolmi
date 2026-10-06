from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.actions import get_registry, invoke
from app.auth import Context


class _Query:
    def __init__(self, rows: list[dict[str, Any]], op: str = "select", data: Any = None) -> None:
        self.rows = rows
        self.op = op
        self.data = data
        self.filters: list[tuple[str, str, Any]] = []

    def select(self, *_a: Any) -> _Query:
        return self

    def eq(self, column: str, value: Any) -> _Query:
        self.filters.append(("eq", column, value))
        return self

    def is_(self, column: str, _null: str) -> _Query:
        self.filters.append(("eq", column, None))
        return self

    def in_(self, column: str, values: list[Any]) -> _Query:
        self.filters.append(("in", column, values))
        return self

    def order(self, *_a: Any, **_k: Any) -> _Query:
        return self

    def limit(self, _n: int) -> _Query:
        return self

    def _matches(self, row: dict[str, Any]) -> bool:
        for kind, column, value in self.filters:
            if kind == "eq" and row.get(column) != value:
                return False
            if kind == "in" and row.get(column) not in value:
                return False
        return True

    def execute(self) -> Any:
        hit = [r for r in self.rows if self._matches(r)]
        if self.op == "update":
            for row in hit:
                row.update(self.data)
        elif self.op == "delete":
            self.rows[:] = [r for r in self.rows if r not in hit]
        elif self.op == "insert":
            self.rows.append(dict(self.data))
            hit = [self.rows[-1]]
        return SimpleNamespace(data=[dict(r) for r in hit])


class _Table:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def select(self, *_a: Any) -> _Query:
        return _Query(self.rows)

    def update(self, data: dict[str, Any]) -> _Query:
        return _Query(self.rows, "update", data)

    def insert(self, data: dict[str, Any]) -> _Query:
        return _Query(self.rows, "insert", data)

    def delete(self) -> _Query:
        return _Query(self.rows, "delete")


class _Client:
    def __init__(self, nodes: list[dict[str, Any]]) -> None:
        self.nodes = nodes

    def table(self, name: str) -> _Table:
        assert name == "nodes"
        return _Table(self.nodes)


def _tree() -> list[dict[str, Any]]:
    return [
        {"id": 1, "parent_id": None, "position": 0},
        {"id": 2, "parent_id": None, "position": 1},
        {"id": 3, "parent_id": 1, "position": 0},
        {"id": 4, "parent_id": 1, "position": 1},
        {"id": 5, "parent_id": 1, "position": 2},
        {"id": 6, "parent_id": 3, "position": 0},
    ]


def _move(nodes: list[dict[str, Any]], **args: Any) -> Any:
    profile = {"id": "u1", "role": "admin", "approved": True}
    ctx = Context(user_id="u1", email=None, profile=profile, client=_Client(nodes))
    return invoke(get_registry()["move_node"], ctx, args)


def _order(nodes: list[dict[str, Any]], parent: int | None) -> list[int]:
    kids = [n for n in nodes if n["parent_id"] == parent]
    return [n["id"] for n in sorted(kids, key=lambda n: n["position"])]


def test_without_a_placement_only_the_parent_changes():
    nodes = _tree()

    row = _move(nodes, node_id=2, parent_id=1)

    assert row["parent_id"] == 1
    assert row["position"] == 1
    assert [n["position"] for n in nodes if n["parent_id"] == 1 and n["id"] != 2] == [0, 1, 2]


def test_first_renumbers_the_siblings():
    nodes = _tree()

    _move(nodes, node_id=2, parent_id=1, placement="first")

    assert _order(nodes, 1) == [2, 3, 4, 5]
    assert sorted(n["position"] for n in nodes if n["parent_id"] == 1) == [0, 1, 2, 3]


def test_after_a_sibling_renumbers_the_siblings():
    nodes = _tree()

    _move(nodes, node_id=2, parent_id=1, placement="after", after_node_id=3)

    assert _order(nodes, 1) == [3, 2, 4, 5]
    assert sorted(n["position"] for n in nodes if n["parent_id"] == 1) == [0, 1, 2, 3]


def test_last_goes_to_the_end():
    nodes = _tree()

    _move(nodes, node_id=3, parent_id=1, placement="last")

    assert _order(nodes, 1) == [4, 5, 3]


def test_after_a_node_that_is_not_a_sibling_is_refused():
    with pytest.raises(HTTPException) as exc:
        _move(_tree(), node_id=2, parent_id=1, placement="after", after_node_id=6)

    assert exc.value.status_code == 422
    assert "Node 6 is not under that parent" in exc.value.detail


def test_a_node_cannot_go_into_its_own_child():
    with pytest.raises(HTTPException) as exc:
        _move(_tree(), node_id=1, parent_id=6)

    assert exc.value.status_code == 422


def test_a_missing_parent_is_a_404():
    with pytest.raises(HTTPException) as exc:
        _move(_tree(), node_id=2, parent_id=99)

    assert exc.value.status_code == 404


def test_a_page_s_content_cannot_be_set_through_update_node():
    profile = {"id": "u1", "role": "admin", "approved": True}
    ctx = Context(user_id="u1", email=None, profile=profile, client=_Client(_tree()))

    for field in ("content_md", "content_web"):
        with pytest.raises(HTTPException) as exc:
            invoke(get_registry()["update_node"], ctx, {"node_id": 1, field: "x"})

        assert exc.value.status_code == 422
        assert field in exc.value.detail
