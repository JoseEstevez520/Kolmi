"""The streamed chat prompt and the generated chat catalogue cannot drift apart."""

from __future__ import annotations

import re

from app.agents import openui
from app.agents.prompts import CHAT_PARTS, chat_stream_system

CALL = re.compile(r"\b([A-Z][A-Za-z]+)\(")


def _components() -> dict:
    return openui.chat_spec()["components"]


def test_chat_parts_exist_in_the_spec():
    assert openui.chat_spec()["root"] == "Answer"
    assert set(CHAT_PARTS) <= set(_components())


def test_every_part_the_prompt_names_is_in_the_spec():
    prompt = chat_stream_system("en")
    listed = prompt.split("Parts (", 1)[1].split("Rules:", 1)[0]
    for name in CALL.findall(listed):
        assert name in _components(), name
    for name in CHAT_PARTS:
        assert _components()[name]["signature"] in prompt


def test_prompt_examples_only_use_spec_parts():
    prompt = chat_stream_system("en")
    example = prompt.split("Example:", 1)[1]
    names = set(CALL.findall(example))
    assert "Answer" in names
    assert names <= set(_components())
