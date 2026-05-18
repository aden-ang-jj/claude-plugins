"""Typed application config loaded from environment variables and .env.

Validation happens once at import time so a misconfigured environment fails
loudly and clearly — not deep inside a request three steps later.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from pydantic_settings import BaseSettings, SettingsConfigDict

Provider = Literal["openai", "openrouter", "deepinfra"]


class ProviderMeta(TypedDict):
    base_url: str | None
    api_key_attr: str
    default_model: str


PROVIDERS: dict[Provider, ProviderMeta] = {
    "openai": {
        "base_url": None,  # SDK default (api.openai.com)
        "api_key_attr": "openai_api_key",
        "default_model": "gpt-4o-mini",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_attr": "openrouter_api_key",
        "default_model": "openai/gpt-4o-mini",
    },
    "deepinfra": {
        "base_url": "https://api.deepinfra.com/v1/openai",
        "api_key_attr": "deepinfra_api_key",
        "default_model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    },
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    llm_provider: Provider = "openrouter"
    llm_default_model: str | None = None
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2

    log_level: str = "INFO"

    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
    deepinfra_api_key: str | None = None

    def api_key_for(self, provider: Provider) -> str:
        meta = PROVIDERS[provider]
        value = getattr(self, meta["api_key_attr"], None)
        if not value:
            env_name = meta["api_key_attr"].upper()
            raise RuntimeError(
                f"Missing API key for provider '{provider}'. "
                f"Set {env_name} in your .env file."
            )
        return value

    def base_url_for(self, provider: Provider) -> str | None:
        return PROVIDERS[provider]["base_url"]

    def default_model_for(self, provider: Provider) -> str:
        return self.llm_default_model or PROVIDERS[provider]["default_model"]


settings = Settings()
