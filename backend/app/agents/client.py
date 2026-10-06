from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any, Callable, Protocol

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


# A guard against a loop that never ends, not a budget: normal use never gets near it. Past it,
# the model is asked to answer with what it has.
MAX_TOOL_ROUNDS = 50
STOP_TOOLS = "No more tool calls. Answer now with the JSON, with what you have."
MAX_EMPTY_ANSWERS = 2
EMPTY_ANSWER = (
    "Your last message had no answer in it. Call a tool if you still need one, or answer now "
    "with the JSON object."
)


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

    def __init__(self, *, api_key: str, base_url: str, model: str, gateway: bool = False) -> None:
        from openai import OpenAI

        self.model = model
        self.gateway = gateway
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
