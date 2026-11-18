"""The AI in a note: its pieces are checked as a page's are, and mended once."""

from __future__ import annotations

from app.actions.chat import AskChatParams, stream_chat
from app.agents.note_pieces import Mend, apply_mends, mend_pieces, piece_problems
from tests.fakes import FakeLLM
from tests.test_chat_stream import _events
from tests.test_chat_tools import _Client, _ctx

GOOD = 'root = Answer([t])\nt = Table(["a", "b"], [["1", "2"]])'
BAD = 'root = Answer([f])\nf = Figure(label = "x", parts = [Chip("A")])'


def _answer(*programs: str) -> str:
    return "%%ask\n## X\nText.\n" + "".join(f"```kolmi-ai\n{p}\n```\n" for p in programs)


def test_a_good_piece_holds_up_and_a_bad_one_says_why():
    assert piece_problems(GOOD) == []
    [problem] = piece_problems(BAD)
    assert "parse" in problem


def test_a_bad_piece_is_mended_once_and_a_good_one_left_alone():
    llm = FakeLLM()
    llm.text_response = [GOOD]
    mends = mend_pieces(llm, _answer(GOOD, BAD), "parts")
    assert mends == [Mend(1, GOOD)]
    assert len([c for c in llm.calls if c[0] == "text"]) == 1
    assert "doesn't parse" in llm.calls[-1][2] or "parse" in llm.calls[-1][2]


def test_a_piece_whose_fix_is_still_broken_is_dropped():
    llm = FakeLLM()
    llm.text_response = [BAD]
    mends = mend_pieces(llm, _answer(BAD), "parts")
    assert mends == [Mend(0, None)]
    assert "kolmi-ai" not in apply_mends(_answer(BAD), mends)
    assert "Text." in apply_mends(_answer(BAD), mends)


def test_mends_go_in_place():
    fixed = apply_mends(_answer(GOOD, BAD), [Mend(1, GOOD)])
    assert fixed.count(GOOD) == 2 and BAD not in fixed


def test_the_stream_sends_a_fix_before_done(monkeypatch):
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = [_answer(BAD)]
    llm.text_response = [GOOD]
    monkeypatch.setattr("app.actions.chat.get_chat_llm", lambda: llm)
    params = AskChatParams(question="what?", mode="note", note="a note")
    events = _events(list(stream_chat(_ctx(client), params)))
    assert [n for n, _ in events][-2:] == ["fix", "done"]
    assert events[-2][1] == {"index": 0, "program": GOOD}
    assert GOOD in client.rows("chat_messages")[0]["answer"]
