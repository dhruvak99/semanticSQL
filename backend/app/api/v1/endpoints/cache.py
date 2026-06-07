from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_cache_entries() -> dict[str, list[object]]:
    return {"items": []}
