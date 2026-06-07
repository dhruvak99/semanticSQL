from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_query_history() -> dict[str, list[object]]:
    return {"items": []}
