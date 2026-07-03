from fastapi import APIRouter

from app.services.research_analytics_service import get_research_analytics

router = APIRouter()


@router.get("/")
def list_research_items() -> dict[str, list[object]]:
    return {"items": []}


@router.get("/analytics")
def research_analytics() -> dict[str, object]:
    return get_research_analytics()
