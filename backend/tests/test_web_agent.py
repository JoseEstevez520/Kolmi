from __future__ import annotations

import pytest

from app.agents import openui
from app.agents.web import write_web
from app.passes.daily import run_daily_pass
from tests.fakes import FakeLLM, FakeStore

PAGE = '''root = Page([intro, h, cmd, tip, steps])
intro = Text("A commit records a snapshot.\\nIt has a message.")
h = Heading("Fix the last commit")
cmd = CodeBlock("git commit --amend", "bash", "terminal")
tip = Callout("warning", "Only amend what you have **not** pushed.")
steps = Steps([s1, s2])
s1 = StepItem("Stage", "Run `git add`.")
s2 = StepItem("Amend", "Run the command above.")
'''


def _note(note_id: int = 1) -> dict:
    return {
        "id": note_id,
        "content": "git commit --amend fixes the last commit",
        "node_id": None,
        "status": "pending",
    }


def _create_plan() -> dict:
    return {
        "batches": [
            {
                "note_ids": [1],
                "action": "create",
                "new_page": {"parent_id": 10, "title": "Git", "description": ""},
                "summary": "How to amend the last commit.",
                "reason": "new topic",
            }
        ],
        "discarded": [],
    }


def _update_plan() -> dict:
    return {
        "batches": [
            {
                "note_ids": [1],
                "action": "update",
                "node_id": 20,
                "summary": "Add amend.",
                "reason": "fits the Git page",
            }
        ],
        "discarded": [],
    }


class BrokenWebLLM(FakeLLM):
    model = "fake-web"

    def complete_text(self, system, user):
        self.calls.append(("text", system, user))
        raise RuntimeError("billing suspended")


# -- the parser and the Markdown view ------------------------------------------------


def test_parses_a_page_with_forward_references():
    root = openui.parse(PAGE)

    assert root.name == "Page"
    assert [block.name for block in root.args[0]] == [
        "Text",
        "Heading",
        "CodeBlock",
        "Callout",
        "Steps",
    ]
    assert root.args[0][0].args[0] == "A commit records a snapshot.\nIt has a message."
    assert openui.unknown_components(root) == set()


def test_derives_markdown_from_the_page():
    markdown = openui.to_markdown(openui.parse(PAGE))

    assert markdown.startswith("A commit records a snapshot.")
    assert "## Fix the last commit" in markdown
    assert '```bash title="terminal"\ngit commit --amend\n```' in markdown
    assert "> [!WARNING]\n> Only amend what you have **not** pushed." in markdown
    assert "1. **Stage**\n   Run `git add`." in markdown


def test_strips_a_code_fence_around_the_page():
    fenced = f"Here it is:\n```openui-lang\n{PAGE}```\n"
    assert openui.parse(fenced).name == "Page"


@pytest.mark.parametrize(
    "source",
    ["", "just some prose", 'root = Text("no page")', 'root = Page([a', "# Markdown\n\ntext"],
)
def test_rejects_what_is_not_a_page(source):
    with pytest.raises(openui.ParseError):
        openui.parse(source)


def test_flags_components_outside_the_catalogue():
    root = openui.parse('root = Page([x])\nx = BarChart(["a"], [])')
    assert openui.unknown_components(root) == {"BarChart"}


def test_the_generated_prompts_are_there():
    assert "Page(" in openui.full_prompt()
    assert "openui:config" in openui.gateway_prompt()
    assert "Page" in openui.component_names()


# -- the web agent in the daily pass -------------------------------------------------


def test_writes_the_page_as_openui_lang():
    store = FakeStore(notes=[_note()], nodes=[])
    llm = FakeLLM(json_response=_create_plan(), text_response="SHOULD NOT BE USED")
    web = FakeLLM(text_response=PAGE)
    web.model = "fake-web"

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    page = next(iter(store._pages.values()))
    assert page["content_web"] == PAGE.strip()
    assert "## Fix the last commit" in page["content_md"]
    assert summary["web_model"] == "fake-web"
    assert summary["web_fallbacks"] == []
    assert summary["pages"][0]["format"] == "web"
    # The gatekeeper ran on the main model; the page was written by the web agent only.
    assert [kind for kind, *_ in llm.calls] == ["json"]
    assert len(web.calls) == 1
    # A plain model (DeepSeek) is sent the whole catalogue.
    assert web.calls[0][1] == openui.full_prompt()
    assert [entry["action"] for entry in store.logs] == ["created"]


def test_updates_a_web_page_and_keeps_the_previous_version():
    old_web = 'root = Page([t])\nt = Text("old")'
    store = FakeStore(
        notes=[_note()],
        nodes=[],
        pages=[{"id": 20, "title": "Git", "content_md": "old", "content_web": old_web}],
    )
    llm = FakeLLM(json_response=_update_plan())
    web = FakeLLM(text_response=PAGE)

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    assert summary["updated"] == 1
    assert store.versions == [{"node_id": 20, "content_md": "old", "content_web": old_web}]
    assert store.page(20)["content_web"] == PAGE.strip()
    # The web agent was handed the current OpenUI Lang to build on.
    assert old_web in web.calls[0][2]
    assert [entry["action"] for entry in store.logs] == ["updated"]


def test_falls_back_to_markdown_when_the_web_agent_fails():
    store = FakeStore(notes=[_note()], nodes=[])
    llm = FakeLLM(json_response=_create_plan(), text_response="# Git\n\nUse `--amend`.")
    web = BrokenWebLLM()

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    assert summary["status"] == "done"
    page = next(iter(store._pages.values()))
    assert page["content_md"] == "# Git\n\nUse `--amend`."
    assert page["content_web"] == ""
    assert summary["pages"][0]["format"] == "markdown"
    assert summary["web_fallbacks"] == [
        {"node_id": page["id"], "reason": "web agent failed: billing suspended"}
    ]
    assert store.pending_notes() == []


def test_falls_back_to_markdown_when_the_web_agent_writes_no_page():
    store = FakeStore(notes=[_note()], nodes=[])
    llm = FakeLLM(json_response=_create_plan(), text_response="# Git\n\nAmend.")
    web = FakeLLM(text_response="Sorry, I can only answer in prose.")

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    page = next(iter(store._pages.values()))
    assert page["content_web"] == ""
    assert page["content_md"] == "# Git\n\nAmend."
    assert summary["web_fallbacks"][0]["reason"].startswith("web agent failed:")


def test_dry_run_does_not_call_the_web_agent():
    store = FakeStore(notes=[_note()], nodes=[])
    web = FakeLLM(text_response=PAGE)

    summary = run_daily_pass(
        store=store, llm=FakeLLM(json_response=_create_plan()), web_llm=web, dry_run=True
    )

    assert summary["status"] == "dry-run"
    assert web.calls == []


def test_the_gateway_gets_its_short_config_block():
    web = FakeLLM(text_response=PAGE)
    web.gateway = True

    write_web(web, title="Git", summary="Use --amend.")

    assert web.calls[0][1] == openui.gateway_prompt()


def test_the_web_agent_is_deepseek_unless_thesys_is_chosen(monkeypatch):
    from app.agents import client
    from app.config import Settings

    def web_for(**values):
        monkeypatch.setattr(client, "get_settings", lambda: Settings(_env_file=None, supabase_url="u", supabase_service_key="s", class_code="c", **values))
        client.get_llm.cache_clear()
        client.get_web_llm.cache_clear()
        return client.get_web_llm()

    try:
        assert web_for(llm_api_key="k").gateway is False
        assert web_for(llm_api_key="k", thesys_api_key="t").gateway is False
        assert web_for(llm_api_key="k", web_provider="thesys", thesys_api_key="t").gateway is True
        # Thesys chosen without a key: DeepSeek writes the page.
        assert web_for(llm_api_key="k", web_provider="thesys").gateway is False
    finally:
        client.get_llm.cache_clear()
        client.get_web_llm.cache_clear()
