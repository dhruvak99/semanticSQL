from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_models() -> dict[str, list[object]]:
    return {"items": []}
