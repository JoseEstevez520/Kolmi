"""The MCP evals stay in step with the tools: every tool a case expects is one its role is offered."""

import json

from evals.run_mcp_evals import CASES, judge, tools_for


def test_every_case_expects_a_tool_its_role_has():
    data = json.loads(CASES.read_text(encoding="utf-8"))
    offered = {role: {t["function"]["name"] for t in tools_for(role)} for role in ("student", "admin")}

    for case in data["cases"]:
        for name in case.get("expect", []) + list(case.get("args", {})):
            assert name in offered[case["role"]], (case["id"], name)


def test_the_judge_checks_the_tool_and_its_arguments():
    case = {"expect": ["write_page"], "args": {"write_page": {"node_id": 5, "mode": "merge"}}}

    assert judge(case, "write_page", {"node_id": 5, "mode": "merge"})[0]
    assert not judge(case, "write_page", {"node_id": 5, "mode": "replace"})[0]
    assert not judge(case, "create_note", {})[0]
    assert judge({"expect": [], "not": ["create_note"]}, None, {})[0]
