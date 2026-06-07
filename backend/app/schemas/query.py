from pydantic import BaseModel, Field


class QueryProcessRequest(BaseModel):
    query: str = Field(..., min_length=1)


class QueryProcessResponse(BaseModel):
    generated_sql: str
    cache_hit: bool
    validation_status: str
    execution_time: float
    rows_returned: int
    results: list[dict[str, str | int | float | bool | None]]
