"""The MCP evals stay in step with the tools: every tool a case expects is one its role is offered."""

import json

from evals.run_mcp_evals import CASES, judge, tools_for


def test_every_case_expects_a_tool_its_role_has():
    data = json.loads(CASES.read_text(encoding="utf-8"))
    offered = {role: {t["function"]["name"] for t in tools_for(role)} for role in ("student", "admin")}

    for case in data["cases"]:
        for name in case.get("expect", []) + list(case.get("args", {})):
            assert name in offered[case["role"]], (case["id"], name)


def test_every_chat_case_expects_a_tool_its_role_is_offered_on_chat():
    from evals import run_chat_evals

    data = json.loads(run_chat_evals.CASES.read_text(encoding="utf-8"))
    offered = {role: {t["function"]["name"] for t in run_chat_evals.tools_for(role)} for role in ("student", "admin")}

    assert {"read_page", "search_web"} <= offered["student"]
    for case in data["cases"]:
        for name in case.get("expect", []) + list(case.get("args", {})):
            assert name in offered[case["role"]], (case["id"], name)


def test_a_student_is_never_expected_to_call_an_admin_tool_in_the_chat():
    from evals import run_chat_evals

    data = json.loads(run_chat_evals.CASES.read_text(encoding="utf-8"))
    admin_only = {t["function"]["name"] for t in run_chat_evals.tools_for("admin")} - {
        t["function"]["name"] for t in run_chat_evals.tools_for("student")
    }

    assert admin_only
    for case in data["cases"]:
        if case["role"] == "student":
            assert not admin_only & set(case.get("expect", [])), case["id"]


def test_the_chat_cases_have_unique_ids_and_a_tree_to_read():
    from evals import run_chat_evals

    data = json.loads(run_chat_evals.CASES.read_text(encoding="utf-8"))
    ids = [c["id"] for c in data["cases"]]

    assert len(ids) == len(set(ids))
    assert run_chat_evals.build_index(data["tree"]).startswith("[1] section")


def test_the_judge_checks_the_tool_and_its_arguments():
    case = {"expect": ["write_page"], "args": {"write_page": {"node_id": 5, "mode": "merge"}}}

    assert judge(case, "write_page", {"node_id": 5, "mode": "merge"})[0]
    assert not judge(case, "write_page", {"node_id": 5, "mode": "replace"})[0]
    assert not judge(case, "create_note", {})[0]
    assert judge({"expect": [], "not": ["create_note"]}, None, {})[0]
