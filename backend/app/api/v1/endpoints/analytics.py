from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_query_analytics() -> dict[str, list[object]]:
    return {"items": []}
