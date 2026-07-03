from fastapi import APIRouter

from app.services.dashboard_service import get_dashboard_metrics

router = APIRouter()


@router.get("/")
def dashboard_metrics() -> dict[str, object]:
    return get_dashboard_metrics()
