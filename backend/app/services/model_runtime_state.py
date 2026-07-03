from threading import Lock

from app.core.config import settings

_active_model = settings.llm_model
_active_model_lock = Lock()


def get_active_model() -> str:
    with _active_model_lock:
        return _active_model


def set_active_model(model: str) -> str:
    global _active_model
    with _active_model_lock:
        _active_model = model
        return _active_model
