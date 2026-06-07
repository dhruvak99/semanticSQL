from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_research_items() -> dict[str, list[object]]:
    return {"items": []}
