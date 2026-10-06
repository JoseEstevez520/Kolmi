from __future__ import annotations

import glob
import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.actions import get_registry, invoke
from app.actions.tools import run_tool
from app.agents import openui
from app.agents.web import page_problems
from app.auth import Context
from tests.test_pages import _Client, _ctx, _nodes, _page

SAMPLES = Path(__file__).resolve().parents[2] / "frontend/src/lib/openui/samples"

GOOD = """root = Page([h, t, tip])
h = Heading("Loops")
t = Text("A **loop** repeats a block.")
tip = Callout("tip", "Prefer for over while when the count is known.", "Rule of thumb")"""

SVG = "<svg viewBox='0 0 10 10'><rect width='10' height='10'/></svg>"


def _write(client, content_web, ctx=None, **extra):
    return invoke(
        get_registry()["write_page_web"],
        ctx or _ctx(client),
        {"node_id": 2, "content_web": content_web, **extra},
    )


def _refused(client, content_web) -> str:
    with pytest.raises(HTTPException) as err:
        _write(client, content_web)
    assert err.value.status_code == 422
    return err.value.detail


# -- the catalogue check ------------------------------------------------------------------------


@pytest.mark.parametrize("path", sorted(glob.glob(str(SAMPLES / "*.oui"))), ids=lambda p: Path(p).name)
def test_the_sample_pages_hold_up(path):
    assert page_problems(Path(path).read_text(encoding="utf-8")) == []


def test_a_good_page_has_no_problems():
    assert openui.problems(GOOD) == []


def test_each_problem_names_its_line_and_what_to_change():
    found = openui.problems(
        'root = Page([t, c])\nt = Text(3)\nc = Callout("hint", "x")'
    )

    assert "Line 2: Text's markdown must be string, not a number: Text(markdown: string)." in found
    assert any(p.startswith("Line 3:") and '"hint"' in p and '"tip"' in p for p in found)


def test_a_component_outside_the_catalogue_is_named():
    found = openui.problems('root = Page([x])\nx = Fancy("y")')

    assert any("Fancy is not in the catalogue" in p and "Callout" in p for p in found)


def test_a_missing_required_argument_shows_the_signature():
    found = openui.problems('root = Page([s])\ns = Steps([StepItem("Install")])')

    assert found == ["Line 2: StepItem needs its text: StepItem(title: string, text: string)."]


def test_a_part_in_the_wrong_place_says_what_it_takes():
    found = openui.problems('root = Page([Chip("a")])')

    assert len(found) == 1 and "can't hold Chip" in found[0] and "Figure" in found[0]


def test_unknown_keys_in_an_object_are_named():
    found = openui.problems(
        'root = Page([c])\nc = Chart("Speed", [ChartSeries("s", [{"x": 1, "y": 2, "w": 3}])])'
    )

    assert any("has no 'w'; it takes: x, y, label" in p for p in found)


def test_a_statement_nothing_uses_would_not_show():
    found = openui.problems('root = Page([h])\nh = Heading("A")\nlost = Text("never shown")')

    assert found == [
        "Line 3: lost is never used, so it won't show; put it in its parent's list, or remove it."
    ]


def test_an_undefined_reference_is_named():
    assert openui.problems("root = Page([h])") == ["Line 1: h is used but never defined."]


def test_a_parse_error_gives_its_line():
    assert openui.problems('root = Page([h])\nh = Heading("A"') == [
        "Line 2: it doesn't parse (expected ',' or ')')."
    ]


@pytest.mark.parametrize("source", ["", "   ", "// only a comment", "root = Page([])"])
def test_a_blank_page_is_a_problem(source):
    assert openui.problems(source)


def test_the_root_must_be_a_page():
    assert openui.problems('root = Heading("A")') == [
        "Line 1: the page must start with root = Page([...]), not Heading(...)."
    ]


def test_a_diagram_needs_its_drawing():
    found = page_problems('root = Page([d])\nd = Diagram("Flow", "a flow")')

    assert found == [
        "The Diagram 'Flow' has no drawing: put it in its svg argument (the 4th), or leave the "
        "Diagram out. A brief alone shows nothing."
    ]


def test_a_drawing_goes_through_the_web_agent_s_checks():
    script = "<svg viewBox='0 0 1 1'><script>alert(1)</script></svg>"
    found = page_problems(f'root = Page([d])\nd = Diagram("Flow", "a flow", null, {json.dumps(script)})')

    assert found == ["The Diagram 'Flow', in its svg: it contains a <script>."]


def test_a_drawn_diagram_holds_up():
    assert page_problems(f'root = Page([d])\nd = Diagram("Flow", "a flow", null, {json.dumps(SVG)})') == []


# -- the action -----------------------------------------------------------------------------------


def test_a_valid_page_is_saved_as_given():
    client = _Client(_nodes())

    _write(client, GOOD)

    assert _page(client)["content_web"] == GOOD


def test_a_code_fence_round_the_page_is_dropped():
    client = _Client(_nodes())

    _write(client, f"```openui\n{GOOD}\n```")

    assert _page(client)["content_web"] == GOOD


def test_the_markdown_stays_as_it_is():
    client = _Client(_nodes())

    _write(client, GOOD)

    assert _page(client)["content_md"] == "old md"


def test_the_previous_version_is_kept():
    client = _Client(_nodes())

    _write(client, GOOD)

    assert client.tables["node_versions"] == [
        {"node_id": 2, "content_md": "old md", "content_web": "old web"}
    ]


def test_who_and_from_where_go_in_the_ai_log():
    client = _Client(_nodes())

    _write(client, GOOD, source_url="https://example.org/figure")

    entry = client.tables["ai_log"][0]
    assert entry["action"] == "updated"
    assert entry["reason"] == "Web written as given from https://example.org/figure"
    assert entry["user_id"] == "u1" and entry["source"] == "mcp"


def test_an_invalid_page_is_refused_and_nothing_changes():
    client = _Client(_nodes())

    detail = _refused(client, 'root = Page([c])\nc = Callout("hint", "x")')

    assert "nothing was saved" in detail and "Line 2:" in detail and "send the whole page again" in detail
    assert _page(client)["content_web"] == "old web"
    assert client.tables["node_versions"] == [] and client.tables["ai_log"] == []


@pytest.mark.parametrize("blank", ["   ", "root = Page([])"])
def test_a_page_is_never_left_blank(blank):
    client = _Client(_nodes())

    _refused(client, blank)

    assert _page(client)["content_web"] == "old web"


def test_empty_content_is_a_422():
    client = _Client(_nodes())

    detail = _refused(client, "")

    assert "content_web" in detail


def test_a_student_cannot_write_a_page_s_web():
    client = _Client(_nodes())
    student = Context(
        user_id="u2", email=None, profile={"id": "u2", "role": "student", "approved": True},
        client=client,
    )

    with pytest.raises(HTTPException) as err:
        _write(client, GOOD, ctx=student)

    assert err.value.status_code == 403
    assert _page(client)["content_web"] == "old web"


def test_a_missing_page_is_a_404():
    with pytest.raises(HTTPException) as err:
        invoke(
            get_registry()["write_page_web"], _ctx(_Client(_nodes())),
            {"node_id": 99, "content_web": GOOD},
        )

    assert err.value.status_code == 404
    assert "list_nodes" in err.value.detail


def test_a_section_is_refused():
    with pytest.raises(HTTPException) as err:
        invoke(
            get_registry()["write_page_web"], _ctx(_Client(_nodes())),
            {"node_id": 1, "content_web": GOOD},
        )

    assert err.value.status_code == 422
    assert "write_page_web writes pages" in err.value.detail


def test_it_is_confirmed_and_offered_to_admins_only():
    action = get_registry()["write_page_web"]

    assert action.requires_confirmation and not action.read_only
    assert action.tool and action.mcp and action.min_role == "admin"


def test_the_tool_answer_carries_no_web():
    client = _Client(_nodes())

    answer = run_tool(_ctx(client), "write_page_web", {"node_id": 2, "content_web": GOOD}, "mcp")

    assert "content_web" not in answer and "Rule of thumb" not in answer
    assert json.loads(answer)["id"] == 2


# -- reading the web ------------------------------------------------------------------------------


def _student(client) -> Context:
    return Context(
        user_id="u2", email=None, profile={"id": "u2", "role": "student", "approved": True},
        client=client,
    )


def test_a_student_can_read_a_page_s_web():
    client = _Client(_nodes())

    answer = run_tool(_student(client), "view_node", {"node_id": 2, "include_web": True}, "mcp")

    assert json.loads(answer)["content_web"] == "old web"


def test_the_web_is_only_there_when_asked_for():
    client = _Client(_nodes())

    answer = run_tool(_student(client), "view_node", {"node_id": 2}, "mcp")

    assert "content_web" not in json.loads(answer)
    assert json.loads(answer)["content_md"] == "old md"


def test_a_web_too_long_for_one_answer_says_it_was_cut():
    nodes = _nodes()
    nodes[1]["content_web"] = "x" * 20_000
    client = _Client(nodes)

    answer = run_tool(_student(client), "view_node", {"node_id": 2, "include_web": True}, "mcp")

    assert "[Cut:" in answer and "not the whole of it" in answer


def test_a_student_cannot_write_the_web_through_a_tool():
    client = _Client(_nodes())

    answer = run_tool(_student(client), "write_page_web", {"node_id": 2, "content_web": GOOD}, "mcp")

    assert answer.startswith("There is no tool write_page_web")
    assert _page(client)["content_web"] == "old web"


def test_write_page_web_points_at_the_read():
    action = get_registry()["write_page_web"]

    assert "include_web" in action.description
