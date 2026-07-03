from fastapi import APIRouter

from app.services.query_analytics_service import get_query_analytics
from app.services.query_history_service import list_history_records
from app.services.validation_analytics_service import get_validation_analytics

router = APIRouter()


@router.get("/analytics")
def query_analytics() -> dict[str, object]:
    return get_query_analytics()


@router.get("/validation-analytics")
def validation_analytics() -> dict[str, object]:
    return get_validation_analytics()


@router.get("/")
def list_query_history(limit: int = 100) -> dict[str, list[dict[str, object]]]:
    return {"items": list_history_records(limit=limit)}
