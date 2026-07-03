from fastapi import APIRouter

from app.services.schema_manager_service import get_database_schema

router = APIRouter()


@router.get("/")
def database_schema() -> dict[str, object]:
    return get_database_schema()
