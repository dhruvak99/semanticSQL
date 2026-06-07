from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_settings() -> dict[str, list[object]]:
    return {"items": []}
