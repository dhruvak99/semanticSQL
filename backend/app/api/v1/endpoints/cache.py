from fastapi import APIRouter

from app.services.semantic_cache_service import get_semantic_cache_service

router = APIRouter()


@router.get("/")
def read_cache_metrics() -> dict[str, object]:
    return get_semantic_cache_service().get_metrics()
