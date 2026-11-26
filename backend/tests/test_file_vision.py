"""Vision is optional and partial transcriptions are never treated as source material."""
from types import SimpleNamespace

import pytest

from app import file_vision


@pytest.mark.parametrize("reason, expected", [("stop", "Visible notes"), ("length", "not been read"), ("content_filter", "not been read")])
def test_image_transcription_checks_completion(monkeypatch, reason, expected):
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(
            finish_reason=reason, message=SimpleNamespace(content="Visible notes"),
        )])
    monkeypatch.setattr(file_vision, "get_settings", lambda: SimpleNamespace(
        vision_model="vision", vision_base_url="https://example.invalid", vision_api_key="key",
        llm_base_url="", llm_api_key="",
    ))
    monkeypatch.setattr(file_vision, "OpenAI", lambda **kwargs: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
    ))
    assert expected in file_vision.describe_image(b"photo", "image/png")
    assert calls[0]["messages"][1]["content"][0]["image_url"]["url"].startswith("data:image/png;base64,")
