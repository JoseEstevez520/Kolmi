from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend configuration, read from the environment (or backend/.env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_service_key: str
    class_code: str
    cors_origins: str = "http://localhost:5173"

    # The language the AI writes the shared notes and pages in, until an admin sets it in the
    # admin panel (stored in the `settings` table). A code from app/class_settings.LANGUAGES.
    class_language: str = "en"

    # The daily pass. Any OpenAI-compatible endpoint works; DeepSeek is the default.
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-flash"

    # The web model, optional: it writes the pages as OpenUI Lang, and when it fails, or isn't
    # set, the model above writes them instead. Any OpenAI-compatible endpoint. web_prompt is
    # "full" (the whole catalogue) or "gateway" for an endpoint that builds the prompt from a
    # short config block, as the OpenUI Gateway does.
    web_api_key: str = ""
    web_base_url: str = ""
    web_model: str = ""
    web_prompt: Literal["full", "gateway"] = "full"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
