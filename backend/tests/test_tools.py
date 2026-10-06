from __future__ import annotations

from app.actions import get_registry
from app.actions.tools import offered, schemas
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
    "list_nodes", "view_node", "create_note", "update_note", "my_notes", "list_schedule_events",
}
STUDENT_CHAT = STUDENT_MCP | {"get_settings"}
SCHEDULE_WRITES = {"create_schedule_event", "update_schedule_event", "delete_schedule_event"}


def test_what_a_student_is_offered():
    assert _names("student", "chat") == STUDENT_CHAT
    assert _names("student", "mcp") == STUDENT_MCP


def test_what_an_admin_is_offered():
    every_tool = {a.name for a in get_registry().values() if a.tool}
    assert len(every_tool) == 18
    assert _names("admin", "chat") == every_tool
    assert _names("admin", "mcp") == every_tool - {"get_settings"} - SCHEDULE_WRITES
    assert len(_names("admin", "mcp")) == 14


def test_the_mcp_only_offers_tools():
    assert all(a.tool for a in get_registry().values() if a.mcp)


def test_some_actions_are_never_tools():
    registry = get_registry()
    for name in ("register_profile", "download_file", "ask_chat", "update_settings", "get_profile"):
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
