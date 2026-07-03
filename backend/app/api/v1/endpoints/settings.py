from fastapi import APIRouter

from app.schemas.settings import CacheThresholdUpdateRequest, CacheThresholdUpdateResponse
from app.services.semantic_cache_service import get_semantic_cache_service
from app.services.settings_service import get_runtime_settings

router = APIRouter()


@router.get("/")
def read_settings() -> dict[str, object]:
    return get_runtime_settings()


@router.put("/cache-threshold", response_model=CacheThresholdUpdateResponse)
def update_cache_threshold(payload: CacheThresholdUpdateRequest) -> CacheThresholdUpdateResponse:
    semantic_cache = get_semantic_cache_service()
    semantic_cache.set_threshold(payload.similarity_threshold)
    return CacheThresholdUpdateResponse(
        similarity_threshold=semantic_cache.get_threshold(),
        message="Semantic cache threshold updated successfully.",
    )
