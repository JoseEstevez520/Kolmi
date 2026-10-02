from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Protocol

from ..config import get_settings


class LLM(Protocol):
    """The bit of the model the pass needs. Swapped for a fake in tests."""

    def complete_json(self, system: str, user: str) -> dict[str, Any]: ...

    def complete_text(self, system: str, user: str) -> str: ...


class OpenAILLM:
    """Any OpenAI-compatible chat endpoint; DeepSeek is the default.

    `gateway` marks the Thesys Gateway, which builds the page prompt from a short config block
    instead of being sent the whole catalogue.
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
def get_web_llm() -> LLM:
    """The web agent's model: DeepSeek by default, or the Thesys Gateway when chosen and keyed."""
    settings = get_settings()
    if settings.web_provider == "thesys" and settings.thesys_api_key:
        return OpenAILLM(
            api_key=settings.thesys_api_key,
            base_url=settings.thesys_base_url,
            model=settings.thesys_model,
            gateway=True,
        )
    return get_llm()


def model_name() -> str:
    return get_settings().llm_model
