"""
Application configuration — reads from .env via pydantic-settings.
All secrets are injected via environment variables; no hardcoded values.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database (defaults to local SQLite for zero-setup local dev, or Supabase Postgres)
    database_url: str = "sqlite+aiosqlite:///./scambot.db"

    # Anthropic
    anthropic_api_key: str = "sk-ant-REPLACE_ME"
    claude_model: str = "claude-sonnet-4-5"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = "+14155238886"

    # App
    app_env: str = "development"
    secret_key: str = "change_me"
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
