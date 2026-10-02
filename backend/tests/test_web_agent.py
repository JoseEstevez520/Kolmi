from __future__ import annotations

import json

import pytest

from app.agents import openui
from app.agents.prompts import notes_system, visual_system
from app.agents.web import draw_visuals, write_web
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


MD = "A commit records a snapshot.\n\n## Fix the last commit\n\n```bash\ngit commit --amend\n```"


class BrokenWebLLM(FakeLLM):
    model = "fake-web"

    def complete_text(self, system, user):
        self.calls.append(("text", system, user))
        raise RuntimeError("billing suspended")


# -- the parser ------------------------------------------------------------------------


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


def test_writes_the_notes_then_the_page_from_them():
    store = FakeStore(notes=[_note()], nodes=[])
    llm = FakeLLM(json_response=_create_plan(), text_response=[MD])
    web = FakeLLM(text_response=PAGE)
    web.model = "fake-web"

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    page = next(iter(store._pages.values()))
    assert page["content_web"] == PAGE.strip()
    # The Markdown is the notes agent's, not a view of the OpenUI.
    assert page["content_md"] == MD
    assert summary["web_model"] == "fake-web"
    assert summary["web_fallbacks"] == []
    assert summary["pages"][0]["format"] == "web"
    # The main model ran the gatekeeper and the notes; the web model wrote the page from them.
    assert [(kind, system) for kind, system, _ in llm.calls] == [
        ("tools", llm.calls[0][1]),
        ("text", notes_system("en")),
    ]
    assert "How to amend the last commit." in llm.calls[1][2]
    assert len(web.calls) == 1
    assert MD in web.calls[0][2]
    assert "How to amend the last commit." not in web.calls[0][2]
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
    llm = FakeLLM(json_response=_update_plan(), text_response=[MD])
    web = FakeLLM(text_response=PAGE)

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    assert summary["updated"] == 1
    # The notes agent was handed the current Markdown to fold the new material into.
    assert "old" in llm.calls[1][2]
    assert store.page(20)["content_md"] == MD
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
    assert summary["pages"][0]["model"] is None
    reason = summary["web_fallbacks"][0]["reason"]
    assert reason.startswith("fake-web failed: billing suspended; fake failed:")
    assert store.pending_notes() == []


def test_a_failed_web_step_keeps_the_previous_web():
    old_web = 'root = Page([t])\nt = Text("old")'
    store = FakeStore(
        notes=[_note()],
        nodes=[],
        pages=[{"id": 20, "title": "Git", "content_md": "old", "content_web": old_web}],
    )
    llm = FakeLLM(json_response=_update_plan(), text_response=[MD, "not a page"])
    web = BrokenWebLLM()

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    # The notes moved on; the good web page is not blanked by the failure.
    assert store.page(20) == {"id": 20, "title": "Git", "content_md": MD, "content_web": old_web}
    assert summary["pages"][0]["format"] == "kept"
    assert len(summary["web_fallbacks"]) == 1


def test_falls_back_to_markdown_when_the_web_agent_writes_no_page():
    store = FakeStore(notes=[_note()], nodes=[])
    llm = FakeLLM(json_response=_create_plan(), text_response="# Git\n\nAmend.")
    web = FakeLLM(text_response="Sorry, I can only answer in prose.")

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    page = next(iter(store._pages.values()))
    assert page["content_web"] == ""
    assert page["content_md"] == "# Git\n\nAmend."
    assert summary["web_fallbacks"][0]["reason"].startswith("fake failed:")


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

    write_web(web, title="Git", markdown="Use --amend.")

    assert web.calls[0][1] == openui.gateway_prompt()


def test_the_main_model_writes_the_page_when_the_web_model_fails():
    store = FakeStore(notes=[_note()], nodes=[])
    llm = FakeLLM(json_response=_create_plan(), text_response=[MD, PAGE])
    web = BrokenWebLLM()

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    page = next(iter(store._pages.values()))
    assert page["content_web"] == PAGE.strip()
    assert summary["pages"][0] == {
        "node_id": page["id"],
        "title": "Git",
        "format": "web",
        "model": "fake",
    }
    assert summary["web_down"] is True
    # The main model was sent the whole catalogue and the notes, as the web model was.
    assert llm.calls[2][1] == openui.full_prompt()
    assert MD in llm.calls[2][2] and MD in web.calls[0][2]


def test_a_failed_web_model_is_not_asked_again_in_the_same_pass():
    plan = _create_plan()
    second = dict(plan["batches"][0], note_ids=[2], new_page={"parent_id": 10, "title": "Rebase", "description": ""})
    plan["batches"].append(second)
    store = FakeStore(notes=[_note(), _note(2)], nodes=[])
    llm = FakeLLM(json_response=plan, text_response=[MD, PAGE, MD, PAGE])
    web = BrokenWebLLM()

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    assert len(web.calls) == 1
    assert [p["model"] for p in summary["pages"]] == ["fake", "fake"]


def test_the_web_model_is_optional_and_generic(monkeypatch):
    from app.agents import client
    from app.config import Settings

    def web_for(**values):
        monkeypatch.setattr(client, "get_settings", lambda: Settings(_env_file=None, supabase_url="u", supabase_service_key="s", class_code="c", **values))
        client.get_llm.cache_clear()
        client.get_web_llm.cache_clear()
        return client.get_web_llm()

    try:
        # Not set: the main model writes the pages.
        assert web_for(llm_api_key="k") is None
        assert web_for(llm_api_key="k", web_api_key="w") is None
        web = web_for(llm_api_key="k", web_api_key="w", web_model="some/model")
        assert (web.model, web.gateway) == ("some/model", False)
        gateway = web_for(
            llm_api_key="k",
            web_api_key="w",
            web_base_url="https://gateway.example/v1",
            web_model="some/model",
            web_prompt="gateway",
        )
        assert gateway.gateway is True
    finally:
        client.get_llm.cache_clear()
        client.get_web_llm.cache_clear()


# -- the rest of the catalogue -------------------------------------------------------------

RICH = r'''root = Page([diff, table, terms, more, cards, logos, term, session, chat, fig])
diff = CodeDiff("a\nb\nc", "a\nB\nc", "App.java")
table = Table(["Scope", "One per"], [["`singleton`", "app"], ["`request`", "request"]])
terms = DescriptionList([DescriptionItem("Bean", "An object Spring creates.")])
more = Accordion([AccordionItem("Edge cases", "Rarely needed.")])
cards = Cards([Card("Spring docs", "The reference.", "https://docs.spring.io")])
logos = Logos(["Java", "Spring Boot"])
term = TerminalReplay([TerminalEntry("./mvnw test", "BUILD SUCCESS", "Run the tests")], "~/shop")
session = AgentReplay([AgentPrompt("Add a check."), AgentStep("Reading A.java", "Read A.java", "file-text"), AgentAnswer("Done.")])
chat = Chat([ChatMessage("user", "What is a bean?"), ChatMessage("assistant", "An object Spring manages.")])
fig = Figure("A request goes to the controller.", [c, a, k], "row")
c = Chip("Browser", "blue", "globe")
a = Arrow("calls")
k = Area("Controller", [Label("@GetMapping", "route")], "violet")
'''


def test_parses_every_component_and_writes_it_back():
    root = openui.parse(RICH)
    assert openui.unknown_components(root) == set()
    again = openui.dump(openui.statements(RICH))
    assert openui.parse(again) == root


# -- the visuals: Diagram and Artifact briefs, drawn by the main model ---------------------

SVG = '<svg viewBox="0 0 640 200"><rect class="diagram-part" width="100" height="40"/></svg>'
HTML = "<!doctype html><html><body><button>Ask</button><script>let n = 0</script></body></html>"

VISUAL_PAGE = '''root = Page([intro, d, art])
intro = Text("Scopes.")
d = Diagram("Two curves", "Draw two curves.", "caption")
art = Artifact("Compare scopes", "Two buttons, one per scope.", 300)
'''


def ScriptedLLM(answers):
    """Answers each text call with the next item: a string, or an exception to raise."""
    return FakeLLM(text_response=list(answers))


def test_draws_each_brief_into_the_page():
    llm = ScriptedLLM([f"```svg\n{SVG}\n```", HTML])

    source, report = write_visuals(llm)

    root = openui.parse(source)
    diagram, artifact = root.args[0][1], root.args[0][2]
    assert diagram.args == ["Two curves", "Draw two curves.", "caption", SVG]
    assert artifact.args == ["Compare scopes", "Two buttons, one per scope.", 300, HTML]
    assert [r["drawn"] for r in report] == [True, True]
    # Each kind gets its own prompt, and the brief.
    assert "<svg>" in llm.calls[0][1] and "Draw two curves." in llm.calls[0][2]
    assert "<!doctype html>" in llm.calls[1][1]


def test_a_bad_drawing_is_sent_back_once_with_its_problem():
    llm = ScriptedLLM(['<svg width="10"><rect/></svg>', SVG, HTML])

    source, report = write_visuals(llm)

    retry = llm.calls[1][2]
    assert "the <svg> has no viewBox" in retry
    assert '<svg width="10"><rect/></svg>' in retry
    assert openui.parse(source).args[0][1].args[3] == SVG
    assert all(r["drawn"] for r in report)


def test_a_failed_call_is_tried_once_more():
    llm = ScriptedLLM([RuntimeError("timeout"), SVG, HTML])

    source, report = write_visuals(llm)

    assert len(llm.calls) == 3
    assert openui.parse(source).args[0][1].args[3] == SVG


def test_a_drawing_that_fails_twice_is_dropped_from_the_page():
    llm = ScriptedLLM(['<svg viewBox="0 0 9 9"><script>x()</script></svg>', RuntimeError("down"), "no html here", "still none"])

    source, report = write_visuals(llm)

    root = openui.parse(source)
    assert [block.name for block in root.args[0]] == ["Text"]
    assert report == [
        {"kind": "Diagram", "label": "Two curves", "drawn": False, "reason": "the call failed: down"},
        {
            "kind": "Artifact",
            "label": "Compare scopes",
            "drawn": False,
            "reason": "the HTML document is incomplete: it must run from <!doctype html> to </html>",
        },
    ]
    assert "it contains a <script>" in llm.calls[1][2]


def test_a_page_without_briefs_is_left_as_it_is():
    llm = ScriptedLLM([])
    drawn = f'root = Page([d])\nd = Diagram("x", "a brief", null, {json.dumps(SVG)})'

    assert draw_visuals(llm, PAGE, language="en") == (PAGE, [])
    assert draw_visuals(llm, drawn, language="en") == (drawn, [])
    assert llm.calls == []


def test_the_pass_records_the_visuals_and_keeps_the_page():
    store = FakeStore(notes=[_note()], nodes=[])
    llm = FakeLLM(json_response=_create_plan(), text_response=["Scopes."] + ["junk"] * 4)
    web = FakeLLM(text_response=VISUAL_PAGE)

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    page = next(iter(store._pages.values()))
    assert summary["pages"][0]["format"] == "web"
    assert [v["drawn"] for v in summary["visuals"]] == [False, False]
    assert summary["visuals"][0]["node_id"] == page["id"]
    assert "Diagram" not in page["content_web"] and "Artifact" not in page["content_web"]
    assert page["content_md"] == "Scopes."


def test_the_pass_runs_gatekeeper_notes_web_then_visuals():
    store = FakeStore(notes=[_note()], nodes=[])
    llm = FakeLLM(json_response=_create_plan(), text_response=[MD, SVG, HTML])
    web = FakeLLM(text_response=VISUAL_PAGE)
    web.calls = llm.calls  # one log for both models, to see the order

    summary = run_daily_pass(store=store, llm=llm, web_llm=web)

    systems = [system for _, system, _ in llm.calls]
    assert systems[1:] == [
        notes_system("en"),
        openui.full_prompt(),
        visual_system("svg", "en"),
        visual_system("html", "en"),
    ]
    # The web is written from the notes, and the visuals get them as context.
    assert all(MD in user for _, _, user in llm.calls[2:])
    page = next(iter(store._pages.values()))
    assert page["content_md"] == MD
    blocks = openui.parse(page["content_web"]).args[0]
    assert (blocks[1].args[3], blocks[2].args[3]) == (SVG, HTML)
    assert [v["drawn"] for v in summary["visuals"]] == [True, True]


OVERLAPPING = (
    '<svg viewBox="0 0 640 200"><g transform="translate(10, 0)">'
    '<text x="100" y="50" class="diagram-label">Qwen3.5</text>'
    '<text x="130" y="52" class="diagram-label">MiniMax M2.5</text></g>'
    '<text x="300" y="150">apart</text></svg>'
)


def test_overlapping_labels_are_sent_back_once():
    llm = ScriptedLLM([OVERLAPPING, SVG, HTML])

    source, report = write_visuals(llm)

    assert 'the labels "Qwen3.5" and "MiniMax M2.5" overlap' in llm.calls[1][2]
    assert openui.parse(source).args[0][1].args[3] == SVG
    assert report[0] == {"kind": "Diagram", "label": "Two curves", "drawn": True, "reason": ""}


def test_a_chart_that_still_overlaps_is_kept_rather_than_dropped():
    llm = ScriptedLLM([OVERLAPPING, OVERLAPPING, HTML])

    source, report = write_visuals(llm)

    assert openui.parse(source).args[0][1].args[3] == OVERLAPPING
    assert report[0]["drawn"] is True and "overlap" in report[0]["reason"]


def test_labels_apart_or_rotated_are_not_flagged():
    apart = (
        '<svg viewBox="0 0 640 200"><text x="10" y="20">One label</text>'
        '<text x="10" y="60">Another one</text>'
        '<text transform="translate(30, 30) rotate(-90)">Axis title over them</text></svg>'
    )
    llm = ScriptedLLM([apart, HTML])

    _, report = write_visuals(llm)

    assert len(llm.calls) == 2 and report[0]["reason"] == ""


def write_visuals(llm):
    return draw_visuals(llm, VISUAL_PAGE, language="en")
