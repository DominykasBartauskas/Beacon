from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings read from environment variables."""

    model_config = SettingsConfigDict(env_prefix="BEACON_", case_sensitive=False)

    cors_origins: list[str] = ["http://localhost:5180"]

    live_news_enabled: bool = True
    news_cache_ttl_seconds: int = 900
    news_fetch_limit: int = 30
    news_request_timeout_seconds: float = 6.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
