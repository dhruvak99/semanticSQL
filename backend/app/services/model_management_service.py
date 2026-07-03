import re
from datetime import UTC, datetime
from typing import Any

import requests
from requests import RequestException

from app.core.config import settings
from app.services.model_runtime_state import get_active_model, set_active_model
from app.services.semantic_cache_service import get_semantic_cache_service

OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


class OllamaUnavailableError(RuntimeError):
    pass


class ModelNotInstalledError(ValueError):
    pass


def get_model_management_state() -> dict[str, Any]:
    models = _get_installed_models()
    active_model = get_active_model()

    return {
        "active_model": active_model,
        "embedding_model": settings.semantic_cache_model_name,
        "semantic_threshold": get_semantic_cache_service().get_threshold(),
        "installed_models_count": len(models),
        "models": [
            {
                "name": model["name"],
                "size": _format_size(int(model.get("size", 0))),
                "modified": _format_relative_time(str(model.get("modified_at", ""))),
                "active": model["name"] == active_model,
            }
            for model in models
        ],
    }


def update_active_model(model: str) -> str:
    installed_model_names = {installed_model["name"] for installed_model in _get_installed_models()}
    if model not in installed_model_names:
        raise ModelNotInstalledError(f"Ollama model '{model}' is not installed.")
    return set_active_model(model)


def _get_installed_models() -> list[dict[str, Any]]:
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=10)
        response.raise_for_status()
    except RequestException as error:
        raise OllamaUnavailableError("Ollama is not running.") from error

    payload = response.json()
    models = payload.get("models", [])
    if not isinstance(models, list):
        raise OllamaUnavailableError("Unable to retrieve installed models.")

    return sorted(
        [model for model in models if isinstance(model, dict) and isinstance(model.get("name"), str)],
        key=lambda model: str(model["name"]).lower(),
    )


def _format_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "Unknown"

    size_gb = size_bytes / 1_000_000_000
    if size_gb >= 1:
        return f"{size_gb:.1f} GB"
    return f"{size_bytes / 1_000_000:.1f} MB"


def _format_relative_time(value: str) -> str:
    modified_at = _parse_ollama_datetime(value)
    if modified_at is None:
        return "Unknown"

    elapsed_seconds = max(0, int((datetime.now(UTC) - modified_at).total_seconds()))
    intervals = (
        ("year", 365 * 24 * 60 * 60),
        ("month", 30 * 24 * 60 * 60),
        ("week", 7 * 24 * 60 * 60),
        ("day", 24 * 60 * 60),
        ("hour", 60 * 60),
        ("minute", 60),
    )
    for label, interval_seconds in intervals:
        count = elapsed_seconds // interval_seconds
        if count:
            suffix = "" if count == 1 else "s"
            return f"{count} {label}{suffix} ago"
    return "Just now"


def _parse_ollama_datetime(value: str) -> datetime | None:
    if not value:
        return None
    normalized = re.sub(r"(\.\d{6})\d+", r"\1", value)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
