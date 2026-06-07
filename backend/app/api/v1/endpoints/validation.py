from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_validation_results() -> dict[str, list[object]]:
    return {"items": []}
