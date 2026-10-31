"""
GitSeance Configuration — Environment & Settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_env: str = "development"
    app_name: str = "GitSeance"
    app_version: str = "1.0.0"

    # GitHub
    github_token: str = ""

    # Google AI Studio (Gemma)
    google_api_key: str = ""

    # TabPFN (Prior Labs API)
    tabpfn_api_key: str = ""

    # SerpApi
    serpapi_key: str = ""

    # ElevenLabs
    elevenlabs_api_key: str = ""

    # Sentry
    sentry_dsn: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
