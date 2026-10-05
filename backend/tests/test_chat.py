from __future__ import annotations

from app.agents.chat import run_chat
from tests.fakes import FakeLLM

NODES = [
    {"id": 10, "parent_id": None, "kind": "section", "title": "Tools", "position": 0},
    {"id": 20, "parent_id": 10, "kind": "page", "title": "Git", "position": 0},
]
PAGES = {20: {"id": 20, "title": "Git", "content_md": "# Git\n\nAmend with `--amend`."}}
ANSWER = {"answer": "Use `git commit --amend`.", "sources": [20]}


def test_it_reads_the_page_it_cites():
    llm = FakeLLM(json_response=ANSWER, tool_rounds=[[("read_page", {"node_id": 20})]])
    result = run_chat(llm, "how do I fix my last commit message?", NODES, read_page=PAGES.get)

    assert result.answer == ANSWER["answer"]
    assert result.sources == [20]
    assert llm.tool_results == [f"Page 20, Git:\n\n{PAGES[20]['content_md']}"]


def test_it_answers_from_the_index_with_no_tools():
    llm = FakeLLM(json_response=ANSWER)
    result = run_chat(llm, "how do I fix my last commit message?", NODES, read_page=None)

    assert result.answer == ANSWER["answer"]
    assert llm.calls[0][0] == "json"


def test_a_failed_tool_loop_falls_back_to_the_index():
    llm = FakeLLM(json_response=ANSWER, tool_error=RuntimeError("down"))
    result = run_chat(llm, "anything?", NODES, read_page=PAGES.get)

    assert result.answer == ANSWER["answer"]
    assert [kind for kind, *_ in llm.calls] == ["tools", "json"]


def test_it_gets_the_timetable_when_the_class_has_one():
    llm = FakeLLM(json_response=ANSWER)
    run_chat(llm, "when's the Git class?", NODES, read_page=None, schedule="- Monday 09:00-10:00: Git")

    _, _, user = llm.calls[0]
    assert "Timetable:\n- Monday 09:00-10:00: Git" in user


def test_no_timetable_line_when_the_class_has_none():
    llm = FakeLLM(json_response=ANSWER)
    run_chat(llm, "anything?", NODES, read_page=None)

    _, _, user = llm.calls[0]
    assert "Timetable" not in user


def test_it_gets_todays_date_when_given_one():
    llm = FakeLLM(json_response=ANSWER)
    run_chat(llm, "what classes do I have tomorrow?", NODES, read_page=None, today="Monday, 2026-10-05")

    _, _, user = llm.calls[0]
    assert "Today: Monday, 2026-10-05" in user


def test_it_searches_the_web_when_a_search_tool_is_given():
    llm = FakeLLM(json_response=ANSWER, tool_rounds=[[("search_web", {"query": "today's date"})]])
    result = run_chat(
        llm, "what's today's date?", NODES, read_page=PAGES.get, search=lambda q: f"Results for {q}"
    )

    assert result.answer == ANSWER["answer"]
    assert llm.tool_results == ["Results for today's date"]


def test_no_search_tool_offered_without_one():
    llm = FakeLLM(json_response=ANSWER)
    run_chat(llm, "anything?", NODES, read_page=PAGES.get, search=None)

    assert llm.offered_tools == [["read_page"]]


def test_search_tool_offered_alongside_read_page():
    llm = FakeLLM(json_response=ANSWER)
    run_chat(llm, "anything?", NODES, read_page=PAGES.get, search=lambda q: "")

    assert llm.offered_tools == [["read_page", "search_web"]]


def test_search_is_on_by_default_no_key_needed():
    llm = FakeLLM(json_response=ANSWER)
    run_chat(llm, "anything?", NODES, read_page=PAGES.get)

    assert llm.offered_tools == [["read_page", "search_web"]]
