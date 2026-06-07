from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_schemas() -> dict[str, list[object]]:
    return {"items": []}
