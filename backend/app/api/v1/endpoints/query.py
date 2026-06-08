from fastapi import APIRouter, HTTPException, status

from app.schemas.query import (
    LLMSQLGenerateRequest,
    LLMSQLGenerateResponse,
    QueryProcessRequest,
    QueryProcessResponse,
)
from app.services.database_service import DatabaseErrorCode, DatabaseServiceError
from app.services.llm_sql_generation_service import LLMSQLGenerationError, generate_sql
from app.services.query_pipeline import process_semantic_query

router = APIRouter()


@router.post("/process", response_model=QueryProcessResponse)
def process_query(payload: QueryProcessRequest) -> QueryProcessResponse:
    try:
        return process_semantic_query(payload.query)
    except LLMSQLGenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "llm_sql_generation_failed", "message": str(error)},
        ) from error
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


@router.post("/llm-generate", response_model=LLMSQLGenerateResponse)
def generate_query_with_llm(payload: LLMSQLGenerateRequest) -> LLMSQLGenerateResponse:
    try:
        generation_result = generate_sql(payload.query)
    except LLMSQLGenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "llm_sql_generation_failed", "message": str(error)},
        ) from error

    return LLMSQLGenerateResponse(
        generated_sql=generation_result.sql,
        generation_mode=generation_result.generation_mode,
    )
