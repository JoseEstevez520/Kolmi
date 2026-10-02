from __future__ import annotations

from types import SimpleNamespace

from app.agents import client as client_module
from app.agents.client import OpenAILLM
from app.agents.gatekeeper import build_index, run_gatekeeper
from app.passes.daily import run_daily_pass
from tests.fakes import FakeLLM, FakeStore

NODES = [
    {"id": 10, "parent_id": None, "kind": "section", "title": "Tools", "position": 0},
    {"id": 20, "parent_id": 10, "kind": "page", "title": "Git", "position": 0},
    {"id": 21, "parent_id": 10, "kind": "page", "title": "Docker", "position": 1},
    {"id": 30, "parent_id": None, "kind": "section", "title": "Java", "position": 1},
    {"id": 31, "parent_id": 30, "kind": "page", "title": "Beans", "position": 0},
]
PAGES = {
    20: {"id": 20, "title": "Git", "content_md": "# Git\n\nAmend with `--amend`."},
    21: {"id": 21, "title": "Docker", "content_md": ""},
    31: {"id": 31, "title": "Beans", "content_md": "# Beans\n\nSpring makes them."},
}
NOTES = [
    {"id": 1, "content": "git stash keeps my changes", "node_id": 31, "status": "pending"},
    {"id": 2, "content": "a bean is a singleton by default", "node_id": None, "status": "pending"},
]
PLAN = {
    "batches": [
        {"note_ids": [1], "action": "update", "node_id": 20, "summary": "stash", "reason": "git"}
    ],
    "discarded": [{"note_id": 2, "reason": "page 31 says it"}],
}


def test_the_index_carries_each_description():
    nodes = [
        {"id": 1, "parent_id": None, "kind": "section", "title": "DWCS", "position": 0,
         "description": "Server-side web development: Spring, Thymeleaf"},
        {"id": 2, "parent_id": 1, "kind": "page", "title": "Scopes", "position": 0},
    ]

    assert build_index(nodes) == (
        "[1] section: DWCS — Server-side web development: Spring, Thymeleaf\n"
        "  [2] page: Scopes"
    )


def test_the_tree_is_an_indented_index():
    assert build_index(NODES) == (
        "[10] section: Tools\n"
        "  [20] page: Git\n"
        "  [21] page: Docker\n"
        "[30] section: Java\n"
        "  [31] page: Beans"
    )


def test_the_gatekeeper_gets_the_index_and_no_page_text():
    llm = FakeLLM(json_response=PLAN)
    run_gatekeeper(llm, NOTES, NODES, read_page=PAGES.get)
    user = llm.calls[0][2]
    assert "  [31] page: Beans" in user
    assert "Spring makes them" not in user and "--amend" not in user


def test_the_hint_reaches_the_gatekeeper():
    llm = FakeLLM(json_response=PLAN)
    run_gatekeeper(llm, NOTES, NODES, read_page=PAGES.get)
    user = llm.calls[0][2]
    assert '"hint": 31' in user and '"hint": null' in user


def test_it_reads_pages_and_then_plans():
    llm = FakeLLM(
        json_response=PLAN,
        tool_rounds=[
            [("read_page", {"node_id": 31}), ("read_page", {"node_id": 20})],
            [("read_page", {"node_id": 10}), ("read_page", {"node_id": 21})],
            [("read_page", {"node_id": 99})],
        ],
    )
    plan = run_gatekeeper(llm, NOTES, NODES, read_page=PAGES.get)

    beans, git, tools, docker, missing = llm.tool_results
    assert "Spring makes them." in beans and "Amend with `--amend`." in git
    assert "[20] page: Git" in tools and "[21] page: Docker" in tools
    assert "still empty" in docker
    assert "no node 99" in missing
    assert plan.reads == [31, 20, 10, 21]
    assert plan.batches[0].node_id == 20 and plan.discarded[0].note_id == 2


def test_without_tools_it_decides_from_the_index():
    llm = FakeLLM(json_response=PLAN, tool_error=RuntimeError("tools not supported"))
    plan = run_gatekeeper(llm, NOTES, NODES, read_page=PAGES.get)

    assert [kind for kind, *_ in llm.calls] == ["tools", "json"]
    assert "[31] page: Beans" in llm.calls[1][2]
    assert plan.batches[0].node_id == 20 and plan.reads == []


def test_the_pass_reads_through_the_store_and_reports_it():
    store = FakeStore(notes=NOTES, nodes=NODES, pages=list(PAGES.values()))
    llm = FakeLLM(json_response=PLAN, tool_rounds=[[("read_page", {"node_id": 31})]])

    summary = run_daily_pass(store=store, llm=llm, dry_run=True)

    assert summary["read"] == [31]
    assert "Spring makes them." in llm.tool_results[0]


def _message(tool_calls=None, content=None):
    return SimpleNamespace(
        tool_calls=tool_calls,
        content=content,
        model_dump=lambda **_: {"role": "assistant", "tool_calls": []},
    )


class _Completions:
    """An endpoint that asks for a tool forever, until it is told to stop."""

    def __init__(self) -> None:
        self.requests: list[dict] = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        if "tools" in kwargs:
            call = SimpleNamespace(
                id="c1", function=SimpleNamespace(name="read_page", arguments='{"node_id": 20}')
            )
            message = _message(tool_calls=[call])
        else:
            message = _message(content='{"batches": [], "discarded": []}')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_a_loop_that_never_ends_is_cut_and_still_answers(monkeypatch):
    monkeypatch.setattr(client_module, "MAX_TOOL_ROUNDS", 5)
    completions = _Completions()
    llm = OpenAILLM.__new__(OpenAILLM)
    llm.model = "fake"
    llm._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    ran = []

    answer = llm.complete_with_tools("sys", "user", [], lambda name, args: ran.append(args) or "ok")

    assert answer == {"batches": [], "discarded": []}
    assert len(ran) == 5
    assert len(completions.requests) == 6 and "tools" not in completions.requests[-1]
    assert completions.requests[-1]["messages"][-1]["content"] == client_module.STOP_TOOLS
