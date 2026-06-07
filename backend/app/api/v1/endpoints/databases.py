from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_databases() -> dict[str, list[object]]:
    return {"items": []}
