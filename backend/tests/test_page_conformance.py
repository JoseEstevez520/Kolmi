"""The same completed-page acceptance cases as the official frontend parser."""
import json
import re
from pathlib import Path

import pytest

from app.agents import openui

CASES = json.loads((Path(__file__).resolve().parents[2] / "shared/page-format-cases.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda item: item["id"])
def test_page_conformance(case):
    assert (not openui.problems(case["source"])) is case["valid"]


def _shape(value):
    if isinstance(value, openui.Node):
        names = re.findall(r"(?:\(|, )(\w+)\??:", openui._spec()["components"][value.name]["signature"])
        return {"typeName": value.name, "props": {key: _shape(arg) for key, arg in zip(names, value.args)}}
    if isinstance(value, list):
        return list(map(_shape, value))
    if isinstance(value, dict):
        return {key: _shape(arg) for key, arg in value.items()}
    return value


@pytest.mark.parametrize("case", [case for case in CASES if case["valid"]], ids=lambda item: item["id"])
def test_page_shape(case):
    assert _shape(openui.parse(case["source"])) == case["shape"]
