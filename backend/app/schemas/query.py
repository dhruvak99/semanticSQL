from pydantic import BaseModel, Field


class QueryProcessRequest(BaseModel):
    query: str = Field(..., min_length=1)


class SQLValidationPayload(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)


class QueryProcessResponse(BaseModel):
    generation_mode: str
    generated_sql: str
    corrected_sql: str | None = None
    executed_sql: str | None = None
    validation: SQLValidationPayload
    cache_hit: bool
    similarity_score: float
    validation_status: str
    validation_errors: list[str] = Field(default_factory=list)
    execution_time: float
    rows_returned: int
    results: list[dict[str, str | int | float | bool | None]]


class LLMSQLGenerateRequest(BaseModel):
    query: str = Field(..., min_length=1)


class LLMSQLGenerateResponse(BaseModel):
    generated_sql: str
    generation_mode: str
