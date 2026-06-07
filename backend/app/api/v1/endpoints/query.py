from fastapi import APIRouter, HTTPException, status

from app.schemas.query import QueryProcessRequest, QueryProcessResponse
from app.services.database_service import DatabaseErrorCode, DatabaseServiceError
from app.services.query_pipeline import process_semantic_query

router = APIRouter()


@router.post("/process", response_model=QueryProcessResponse)
def process_query(payload: QueryProcessRequest) -> QueryProcessResponse:
    try:
        return process_semantic_query(payload.query)
    except DatabaseServiceError as error:
        if error.code == DatabaseErrorCode.CONNECTION_FAILED:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        elif error.code in {DatabaseErrorCode.INVALID_SQL, DatabaseErrorCode.UNSAFE_SQL}:
            http_status = status.HTTP_400_BAD_REQUEST
        else:
            http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code.value, "message": error.message},
        ) from error
