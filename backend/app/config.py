from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    youtube_api_key: str = ""
    deepl_api_key: str = ""
    database_url: str = f"sqlite:///{BACKEND_DIR / 'llmp.db'}"

    # Crowdsourced offset behavior. Threshold is the minimum number of
    # submissions required before the median is applied; setting it very
    # high effectively disables community correction (per AGENTS.md §3).
    offset_min_submissions: int = 9999
    offset_enabled: bool = False

    # Per-instance salt used when hashing submitter IPs.
    ip_hash_salt: str = "llmp-dev-salt"

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
