from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.model_management_service import (
    ModelNotInstalledError,
    OllamaUnavailableError,
    get_model_management_state,
    update_active_model,
)

router = APIRouter()


class ActiveModelRequest(BaseModel):
    model: str


@router.get("/")
def model_management_state() -> dict[str, object]:
    try:
        return get_model_management_state()
    except OllamaUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@router.post("/active-model")
def set_active_sql_generation_model(payload: ActiveModelRequest) -> dict[str, str]:
    try:
        active_model = update_active_model(payload.model)
    except ModelNotInstalledError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except OllamaUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error

    return {
        "message": "Active model updated successfully.",
        "active_model": active_model,
    }
