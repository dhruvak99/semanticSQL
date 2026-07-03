from fastapi import APIRouter

from app.services.system_monitor_service import get_system_monitor_metrics

router = APIRouter()


@router.get("/")
def system_monitor_metrics() -> dict[str, object]:
    return get_system_monitor_metrics()
