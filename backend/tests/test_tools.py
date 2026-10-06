from __future__ import annotations

import json

from pydantic import BaseModel

from app.actions import Action, get_registry
from app.actions.tools import TOOL_ANSWER_CHARS, answer, light, offered, run_tool, schemas
from app.auth import Context


def _ctx(role: str) -> Context:
    return Context(
        user_id="u1",
        email=None,
        profile={"id": "u1", "role": role, "approved": True},
        client=None,  # type: ignore[arg-type]
    )


def _names(role: str, surface: str) -> set[str]:
    return {a.name for a in offered(_ctx(role), surface)}  # type: ignore[arg-type]


STUDENT_MCP = {
    "list_nodes", "view_node", "search_pages", "list_schedule_events",
    "create_note", "update_note", "my_notes", "delete_note",
}
STUDENT_CHAT = STUDENT_MCP | {"get_settings", "update_my_name"}
# The class's people are managed in the app and the chat, never over the MCP.
PEOPLE = {"list_users", "set_role", "set_status", "delete_user", "update_my_name"}


def test_what_a_student_is_offered():
    assert _names("student", "chat") == STUDENT_CHAT
    assert _names("student", "mcp") == STUDENT_MCP


def test_what_an_admin_is_offered():
    every_tool = {a.name for a in get_registry().values() if a.tool}
    assert len(every_tool) == 30
    assert _names("admin", "chat") == every_tool
    assert _names("admin", "mcp") == every_tool - {"get_settings"} - PEOPLE
    assert len(_names("admin", "mcp")) == 24


def test_the_mcp_only_offers_tools():
    assert all(a.tool for a in get_registry().values() if a.mcp)


def test_some_actions_are_never_tools():
    registry = get_registry()
    for name in ("register_profile", "download_file", "ask_chat", "update_settings", "get_profile", "delete_my_account"):
        assert not registry[name].tool
    for name in ("update_settings", "get_settings", "register_profile", "get_profile"):
        assert not registry[name].mcp


def test_every_get_action_is_read_only():
    assert all(a.read_only for a in get_registry().values() if a.method == "GET")


def test_schemas_are_functions_named_after_what_is_offered():
    names = _names("admin", "chat")
    found = schemas(_ctx("admin"), "chat")  # type: ignore[arg-type]
    assert {s["function"]["name"] for s in found} == names
    assert all(s["type"] == "function" for s in found)


def test_every_tool_is_described_for_a_model():
    for action in get_registry().values():
        if not action.tool:
            continue
        assert len(action.description) > 40, action.name
        if action.params is None:
            continue
        for field, schema in action.params.model_json_schema()["properties"].items():
            assert schema.get("description"), f"{action.name}.{field}"


# -- what goes back to the model -----------------------------------------------------


class _Out(BaseModel):
    id: int
    content_web: str = "big"


def test_light_drops_the_web_content_at_any_depth():
    value = [{"id": 1, "content_web": "x", "kids": [{"content_web": "y", "title": "T"}]}, _Out(id=2)]

    assert light(value) == [{"id": 1, "kids": [{"title": "T"}]}, {"id": 2}]


def test_a_short_answer_is_json_as_it_is():
    assert answer({"title": "Introducción"}) == '{"title": "Introducción"}'


def test_a_long_answer_is_cut_and_says_how_to_ask_for_less():
    value = {"content_md": "x" * (TOOL_ANSWER_CHARS + 500)}
    full = len(json.dumps(value))
    text = answer(value)

    assert text.startswith('{"content_md": "xxx')
    body, note = text.split("\n[Cut: ")
    assert len(body) == TOOL_ANSWER_CHARS
    assert note.startswith(f"{full - TOOL_ANSWER_CHARS} more characters. Ask for less")


def test_run_tool_answers_with_the_light_json():
    registry = get_registry()
    probe = Action(
        name="probe", description="d", handler=lambda _c, _p: {"id": 1, "content_web": "x"}, tool=True
    )
    registry["probe"] = probe
    try:
        assert run_tool(_ctx("student"), "probe", None, "chat") == '{"id": 1}'  # type: ignore[arg-type]
    finally:
        del registry["probe"]


def test_run_tool_refuses_what_is_not_offered():
    for name in ("delete_node", "update_settings", "nope"):
        text = run_tool(_ctx("student"), name, {}, "chat")  # type: ignore[arg-type]
        assert text == f"There is no tool {name}. The tools you have are the ones listed."


def test_run_tool_turns_an_error_into_text():
    text = run_tool(_ctx("student"), "view_node", {"node_id": "abc"}, "chat")  # type: ignore[arg-type]

    assert text.startswith("Error 422: Invalid params. node_id")
