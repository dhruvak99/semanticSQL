import platform
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import requests
from requests import RequestException

from app.core.config import settings
from app.db.session import engine
from app.services.llm_sql_generation_service import OLLAMA_GENERATE_URL
from app.services.model_management_service import OLLAMA_TAGS_URL
from app.services.model_runtime_state import get_active_model
from app.services.semantic_cache_service import get_semantic_cache_service


def get_runtime_settings() -> dict[str, Any]:
    semantic_cache = get_semantic_cache_service()

    return {
        "active_llm_model": get_active_model(),
        "embedding_model": settings.semantic_cache_model_name,
        "cache_backend": semantic_cache.backend_name,
        "redis_url": settings.redis_url,
        "similarity_threshold": semantic_cache.get_threshold(),
        "ollama_url": OLLAMA_GENERATE_URL,
        "database_engine": _format_database_engine(engine.url.get_backend_name()),
        "database_url": engine.url.render_as_string(hide_password=False),
        "python_version": platform.python_version(),
        "semantic_sql_version": _get_semantic_sql_version(),
        "operating_system": platform.platform(),
        "ollama_available": _ollama_is_available(),
        "redis_available": semantic_cache.redis_available,
    }


def _ollama_is_available() -> bool:
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=3)
        response.raise_for_status()
    except RequestException:
        return False
    return True


def _get_semantic_sql_version() -> str:
    try:
        return version("semanticsql-backend")
    except PackageNotFoundError:
        return "0.1.0"


def _format_database_engine(backend_name: str) -> str:
    normalized_name = backend_name.lower()
    if normalized_name == "sqlite":
        return "SQLite"
    if normalized_name == "mysql":
        return "MySQL"
    return backend_name
