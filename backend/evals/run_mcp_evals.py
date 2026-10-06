"""Do the MCP's tool descriptions lead a model to the right tool?

Each case in mcp_tools.json is a request a member might make of their own AI, with the tool (and
arguments) its first call should go to. The model gets the tools exactly as /mcp lists them for
that role (names, descriptions, input schemas), the server's instructions, and the class's tree
(as if it had read list_nodes already), then the request. Only its first tool call is judged.

Run from backend/, with the model's settings in the environment or backend/.env (LLM_API_KEY,
LLM_BASE_URL, LLM_MODEL, as for the daily pass), or another model's with --model / --base-url:

    .venv/bin/python -m evals.run_mcp_evals
    .venv/bin/python -m evals.run_mcp_evals --role student --repeat 3
    .venv/bin/python -m evals.run_mcp_evals --only admin-merge --verbose

It calls no Kolmi tool and touches no database: it only asks the model which tool it would call.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# The settings need these to load; nothing here reaches Supabase.
for name, value in (("SUPABASE_URL", "http://localhost"), ("SUPABASE_SERVICE_KEY", "eval"), ("CLASS_CODE", "eval")):
    os.environ.setdefault(name, value)

from app.actions.tools import offered  # noqa: E402
from app.auth import Context  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.mcp_server import INSTRUCTIONS, _tool  # noqa: E402

CASES = Path(__file__).with_name("mcp_tools.json")


def tools_for(role: str) -> list[dict[str, Any]]:
    """The role's tools as /mcp lists them, in the function-calling shape a chat API takes."""
    ctx = Context(user_id="eval", email=None, profile={"role": role, "status": "active"}, client=None, source="mcp")  # type: ignore[arg-type]
    return [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.input_schema}}
        for t in (_tool(action) for action in offered(ctx, "mcp"))
    ]


def matches(value: Any, want: Any) -> bool:
    if isinstance(want, dict) and "contains" in want:
        return isinstance(value, str) and want["contains"].lower() in value.lower()
    if isinstance(want, dict) and "present" in want:
        return value is not None
    return value == want


def judge(case: dict[str, Any], name: str | None, args: dict[str, Any]) -> tuple[bool, str]:
    expect, avoid = case.get("expect", []), case.get("not", [])
    if name in avoid:
        return False, f"called {name}, which it should not"
    if not expect:
        return (name is None), "no call, as wanted" if name is None else f"called {name}; no call wanted"
    if name not in expect:
        return False, f"called {name or 'nothing'}; wanted {' or '.join(expect)}"
    for key, want in case.get("args", {}).get(name, {}).items():
        if not matches(args.get(key), want):
            return False, f"{name}: {key} was {args.get(key)!r}; wanted {want!r}"
    return True, f"{name}"


def ask(client, model: str, tree: str, case: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    system = f"{INSTRUCTIONS}\n\nThe class's tree, from list_nodes:\n{tree}"
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": case["request"]}],
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
