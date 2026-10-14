from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any, Callable, Iterator, Protocol

from ..config import get_settings

log = logging.getLogger(__name__)


class LLM(Protocol):
    """The bit of the model the pass needs. Swapped for a fake in tests."""

    def complete_json(self, system: str, user: str) -> dict[str, Any]: ...

    def complete_text(self, system: str, user: str) -> str: ...

    def complete_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        run_tool: Callable[[str, dict[str, Any]], str],
    ) -> dict[str, Any]:
        """Let the model call `tools` (each answered by `run_tool`) until it answers JSON."""
        ...

    def stream_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        run_tool: Callable[[str, dict[str, Any]], str],
        max_rounds: int = ...,
    ) -> Iterator[dict[str, str]]:
        """Like `complete_with_tools`, but the answer is plain text, streamed. Yields
        `{"type": "status", "text": ...}` when a tool runs and `{"type": "token", "text": ...}`
        for each piece of the answer."""
        ...


# A guard against a loop that never ends, not a budget: normal use never gets near it. Past it,
# the model is asked to answer with what it has.
MAX_TOOL_ROUNDS = 50
STOP_TOOLS = "No more tool calls. Answer now with the JSON, with what you have."
MAX_EMPTY_ANSWERS = 2
EMPTY_ANSWER = (
    "Your last message had no answer in it. Call a tool if you still need one, or answer now "
    "with the JSON object."
)
STOP_TOOLS_TEXT = "No more tool calls. Answer now, with what you have."
EMPTY_ANSWER_TEXT = (
    "Your last message had no answer in it. Call a tool if you still need one, or answer now."
)


def tool_status(name: str, args: dict[str, Any]) -> str:
    """A short line for the person about the tool the model is running."""
    if name == "read_page":
        return f"Reading page {args['node_id']}..." if "node_id" in args else "Reading a page..."
    if name == "search_web":
        return "Searching the web..."
    return f"Using {name.replace('_', ' ')}..."


def _json_object(content: str | None) -> dict[str, Any] | None:
    """The model's reply as a JSON object, or None when it is blank or isn't one."""
    try:
        value = json.loads(content or "")
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


class OpenAILLM:
    """Any OpenAI-compatible chat endpoint; DeepSeek is the default.

    `gateway` marks an endpoint that builds the page prompt from a short config block (the
    OpenUI Gateway) instead of being sent the whole catalogue.
    """

    def __init__(
        self, *, api_key: str, base_url: str, model: str, gateway: bool = False, thinking: bool = True
    ) -> None:
        from openai import OpenAI

        self.model = model
        self.gateway = gateway
        # Only DeepSeek's endpoint knows the `thinking` switch; another one would reject it.
        self._no_thinking = (
            {"thinking": {"type": "disabled"}} if not thinking and "deepseek" in base_url else None
        )
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    def complete_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        run_tool: Callable[[str, dict[str, Any]], str],
    ) -> dict[str, Any]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        empty_answers = 0
        for _ in range(MAX_TOOL_ROUNDS):
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            message = response.choices[0].message
            if not message.tool_calls:
                answer = _json_object(message.content)
                if answer is not None:
                    return answer
                # JSON mode sometimes answers with nothing but blanks after a tool's result: ask
                # again, a couple of times, before giving up.
                empty_answers += 1
                if empty_answers > MAX_EMPTY_ANSWERS:
                    raise ValueError("the model answered without a JSON object")
                messages.append({"role": "user", "content": EMPTY_ANSWER})
                continue
            messages.append(message.model_dump(exclude_none=True))
            for call in message.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except ValueError:
                    args = {}
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": run_tool(call.function.name, args),
                    }
                )
        log.warning("still calling tools after %d rounds; asking for the answer", MAX_TOOL_ROUNDS)
        messages.append({"role": "user", "content": STOP_TOOLS})
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content or "{}")

    def stream_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        run_tool: Callable[[str, dict[str, Any]], str],
        max_rounds: int = MAX_TOOL_ROUNDS,
    ) -> Iterator[dict[str, str]]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        empty_answers = 0
        for _ in range(max_rounds):
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                temperature=0.2,
                stream=True,
                extra_body=self._no_thinking,
            )
            text = ""
            calls: dict[int, dict[str, str]] = {}
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                # Tool calls arrive in pieces, told apart by their index.
                for piece in getattr(delta, "tool_calls", None) or []:
                    call = calls.setdefault(piece.index, {"id": "", "name": "", "arguments": ""})
                    call["id"] = piece.id or call["id"]
                    if piece.function:
                        if piece.function.name and not call["name"]:
                            # Said as soon as the model picks a tool, not when its round ends.
                            yield {"type": "status", "text": tool_status(piece.function.name, {})}
                        call["name"] += piece.function.name or ""
                        call["arguments"] += piece.function.arguments or ""
                if delta.content and not calls:
                    text += delta.content
                    yield {"type": "token", "text": delta.content}
            if not calls:
                if text.strip():
                    return
                empty_answers += 1
                if empty_answers > MAX_EMPTY_ANSWERS:
                    raise ValueError("the model answered with nothing")
                messages.append({"role": "user", "content": EMPTY_ANSWER_TEXT})
                continue
            ordered = [calls[i] for i in sorted(calls)]
            messages.append(
                {
                    "role": "assistant",
                    "content": text or None,
                    "tool_calls": [
                        {
                            "id": c["id"],
                            "type": "function",
                            "function": {"name": c["name"], "arguments": c["arguments"]},
                        }
                        for c in ordered
                    ],
                }
            )
            for call in ordered:
                try:
                    args = json.loads(call["arguments"] or "{}")
                except ValueError:
                    args = {}
                if not isinstance(args, dict):
                    args = {}
                yield {"type": "status", "text": tool_status(call["name"], args)}
                messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": run_tool(call["name"], args)}
                )
        log.warning("still calling tools after %d rounds; asking for the answer", max_rounds)
        messages.append({"role": "user", "content": STOP_TOOLS_TEXT})
        final = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            stream=True,
            extra_body=self._no_thinking,
        )
        for chunk in final:
            if chunk.choices and chunk.choices[0].delta.content:
                yield {"type": "token", "text": chunk.choices[0].delta.content}

    def complete_text(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


@lru_cache
def get_llm() -> LLM:
    settings = get_settings()
    return OpenAILLM(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )


@lru_cache
def get_chat_llm() -> LLM:
    """The model the chat answers with: `chat_model` when it is set, else the main one."""
    settings = get_settings()
    return OpenAILLM(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.chat_model or settings.llm_model,
        thinking=settings.chat_thinking,
    )


@lru_cache
def get_web_llm() -> LLM | None:
    """The web model, when one is set; otherwise the main model writes the pages."""
    settings = get_settings()
    if not (settings.web_api_key and settings.web_model):
        return None
    return OpenAILLM(
        api_key=settings.web_api_key,
        base_url=settings.web_base_url or settings.llm_base_url,
        model=settings.web_model,
        gateway=settings.web_prompt == "gateway",
    )


def model_name() -> str:
    return get_settings().llm_model
