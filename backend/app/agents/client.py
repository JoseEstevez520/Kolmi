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
                return json.loads(message.content or "{}")
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
