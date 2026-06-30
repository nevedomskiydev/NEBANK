"""Central configuration. All secrets come from the environment (.env)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---
    app_name: str = "NEBANK"
    env: str = Field(default="production")
    debug: bool = Field(default=False)

    # Public origin of the Mini App (HTTPS). Used for WebApp button + webhook.
    public_base_url: str = Field(default="https://104-194-143-122.sslip.io")

    # --- Telegram ---
    bot_token: str = Field(default="")  # @nebanknebot token from BotFather (required at runtime)
    bot_username: str = Field(default="nebanknebot")
    # Secret path segment for the webhook; also sent as secret_token header.
    webhook_secret: str = Field(default="nebank-webhook")
    use_webhook: bool = Field(default=True)

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://nebank:nebank@db:5432/nebank"
    )

    # --- Monetization ---
    premium_price_stars: int = Field(default=250)
    premium_period_days: int = Field(default=30)

    # --- Optional AI providers (graceful degradation if unset) ---
    # Voice transcription: "whisper_api" | "faster_whisper" | "off"
    voice_provider: str = Field(default="faster_whisper")
    whisper_api_base: str = Field(default="https://api.openai.com/v1")
    whisper_api_key: str = Field(default="")
    whisper_model: str = Field(default="base")  # for faster-whisper local
    # Optional vision/LLM augmentation for OCR & parsing edge cases.
    llm_api_base: str = Field(default="https://api.openai.com/v1")
    llm_api_key: str = Field(default="")
    llm_model: str = Field(default="gpt-4o-mini")

    # --- Rates ---
    coingecko_base: str = Field(default="https://api.coingecko.com/api/v3")
    fiat_rates_base: str = Field(default="https://api.frankfurter.dev/v1")
    rates_cache_ttl: int = Field(default=300)  # seconds

    # --- Security ---
    initdata_max_age: int = Field(default=86400)  # WebApp auth freshness window (s)

    @property
    def webhook_path(self) -> str:
        return f"/bot/{self.webhook_secret}"

    @property
    def webhook_url(self) -> str:
        return f"{self.public_base_url}{self.webhook_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
