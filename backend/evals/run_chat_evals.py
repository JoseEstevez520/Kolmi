"""Does the web chat's tool list lead a model to the right first call?

Each case in chat_tools.json is a request a student or an admin might make in the chat, with the
tool (and arguments) its first call should go to. The model gets what the chat gives it: the
chat's system prompt (plus the actions prompt, once there is one), the tree as an index and the
question, with `read_page`, `search_web` and the registry's tools offered on "chat" for the
role. A write is a proposal the person confirms, so only the first call is judged, with the
same judge as the MCP evals.

Run from backend/, with the model's settings in the environment or backend/.env (LLM_API_KEY,
LLM_BASE_URL, LLM_MODEL), or another model's with --model / --base-url:

    .venv/bin/python -m evals.run_chat_evals
    .venv/bin/python -m evals.run_chat_evals --role student --repeat 3
    .venv/bin/python -m evals.run_chat_evals --only admin-move-es --verbose

It calls no Kolmi tool and touches no database: it only asks the model which tool it would call.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from evals.run_mcp_evals import judge  # also sets the settings the imports below need

from app.actions.tools import offered  # noqa: E402
from app.agents import prompts  # noqa: E402
from app.agents.search import SEARCH_WEB_TOOL  # noqa: E402
from app.agents.tree import READ_PAGE_TOOL, build_index  # noqa: E402
from app.auth import Context  # noqa: E402
from app.class_settings import FALLBACK_LANGUAGE  # noqa: E402
from app.config import get_settings  # noqa: E402

CASES = Path(__file__).with_name("chat_tools.json")


def tools_for(role: str) -> list[dict[str, Any]]:
    """The role's tools as the chat offers them: read_page, search_web and the registry's."""
    profile = {"role": role, "status": "active"}
    ctx = Context(user_id="eval", email=None, profile=profile, client=None, source="chat")  # type: ignore[arg-type]
    return [READ_PAGE_TOOL, SEARCH_WEB_TOOL] + [a.tool_schema() for a in offered(ctx, "chat")]


def system_prompt(language: str = FALLBACK_LANGUAGE) -> str:
    actions = getattr(prompts, "CHAT_ACTIONS", "")  # added to the chat's prompt by its own change
    return prompts.chat_system(language) + (f"\n\n{actions}" if actions else "")


def ask(client, model: str, nodes: list[dict[str, Any]], case: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    user = f"Tree:\n{build_index(nodes)}\n\nQuestion: {case['request']}"
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt()}, {"role": "user", "content": user}],
        tools=tools_for(case["role"]),
        temperature=0,
    )
    calls = response.choices[0].message.tool_calls or []
    if not calls:
        return None, {}
    try:
        args = json.loads(calls[0].function.arguments or "{}")
    except ValueError:
        args = {}
    return calls[0].function.name, args


def main() -> int:
    from openai import OpenAI

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", help="the model; LLM_MODEL by default")
    parser.add_argument("--base-url", help="an OpenAI-compatible endpoint; LLM_BASE_URL by default")
    parser.add_argument("--api-key-env", default="LLM_API_KEY", help="the variable holding the key")
    parser.add_argument("--role", choices=["student", "admin"], help="only this role's cases")
    parser.add_argument("--only", help="only the case with this id")
    parser.add_argument("--repeat", type=int, default=1, help="ask each case this many times")
    parser.add_argument("--verbose", action="store_true", help="print each call's arguments")
    options = parser.parse_args()

    settings = get_settings()
    key = os.environ.get(options.api_key_env) or settings.llm_api_key
    if not key:
        print(f"No key: set {options.api_key_env} (or LLM_API_KEY in backend/.env).", file=sys.stderr)
        return 2
    client = OpenAI(api_key=key, base_url=options.base_url or settings.llm_base_url)
    model = options.model or settings.llm_model

    data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = [
        c for c in data["cases"]
        if (not options.role or c["role"] == options.role) and (not options.only or c["id"] == options.only)
    ]
    passed = total = 0
    for case in cases:
        for _ in range(options.repeat):
            name, args = ask(client, model, data["tree"], case)
            ok, why = judge(case, name, args)
            passed, total = passed + ok, total + 1
            print(f"{'PASS' if ok else 'FAIL'}  {case['role']:7}  {case['id']:26}  {why}")
            if options.verbose and name:
                print(f"        {json.dumps(args, ensure_ascii=False)}")
    print(f"\n{passed}/{total} passed with {model}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
