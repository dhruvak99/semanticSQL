from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_queries() -> dict[str, list[object]]:
    return {"items": []}
