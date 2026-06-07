from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_DATABASE_URL = f"sqlite+pysqlite:///{BACKEND_DIR / 'semanticsql.db'}"


class Settings(BaseSettings):
    app_name: str = "SemanticSQL API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    backend_cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str] | Any:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or DEFAULT_SQLITE_DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
