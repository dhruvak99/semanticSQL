from typing import Any

from sqlalchemy import desc, select

from app.db.session import SessionLocal
from app.models.query_history import QueryHistory


def create_history_record(
    *,
    natural_language_query: str,
    generated_sql: str,
    generation_mode: str,
    cache_status: str,
    validation_status: str,
    execution_time: float,
    rows_returned: int,
) -> QueryHistory:
    with SessionLocal() as session:
        history_record = QueryHistory(
            natural_language_query=natural_language_query,
            generated_sql=generated_sql,
            generation_mode=normalize_generation_mode(generation_mode),
            cache_status=cache_status,
            validation_status=validation_status,
            execution_time=execution_time,
            rows_returned=rows_returned,
        )
        session.add(history_record)
        session.commit()
        session.refresh(history_record)
        return history_record


def list_history_records(limit: int = 100) -> list[dict[str, Any]]:
    with SessionLocal() as session:
        records = session.execute(
            select(QueryHistory)
            .order_by(desc(QueryHistory.created_at), desc(QueryHistory.id))
            .limit(limit)
        ).scalars().all()

        return [_serialize_history_record(record) for record in records]


def _serialize_history_record(record: QueryHistory) -> dict[str, Any]:
    return {
        "id": record.id,
        "natural_language_query": record.natural_language_query,
        "generated_sql": record.generated_sql,
        "generation_mode": normalize_generation_mode(record.generation_mode),
        "cache_status": record.cache_status,
        "validation_status": record.validation_status,
        "execution_time": record.execution_time,
        "rows_returned": record.rows_returned,
        "created_at": record.created_at.isoformat(),
    }


def normalize_generation_mode(generation_mode: str) -> str:
    return "LLM" if generation_mode.lower() == "llm" else "Rule"
