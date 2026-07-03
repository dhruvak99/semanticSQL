from typing import Any

from sqlalchemy import desc, select

from app.db.session import SessionLocal
from app.models.query_history import QueryHistory
from app.services.query_history_service import _serialize_history_record


def get_validation_analytics(limit: int = 25) -> dict[str, Any]:
    with SessionLocal() as session:
        records = session.execute(
            select(QueryHistory).order_by(desc(QueryHistory.created_at), desc(QueryHistory.id))
        ).scalars().all()

    total_validated_queries = len(records)
    valid_queries = sum(1 for record in records if _is_valid(record.validation_status))
    invalid_queries = total_validated_queries - valid_queries
    schema_mismatch_count = sum(1 for record in records if _is_schema_mismatch(record))
    cache_hit_count = sum(1 for record in records if record.cache_status.lower() == "hit")
    cache_miss_count = total_validated_queries - cache_hit_count
    validation_success_rate = (
        (valid_queries / total_validated_queries) * 100
        if total_validated_queries
        else 0.0
    )
    recent_failures = [
        _serialize_failure_record(record)
        for record in records
        if not _is_valid(record.validation_status)
    ][:limit]

    return {
        "total_validated_queries": total_validated_queries,
        "valid_queries": valid_queries,
        "invalid_queries": invalid_queries,
        "validation_success_rate": round(validation_success_rate, 1),
        "schema_mismatch_count": schema_mismatch_count,
        "cache_hit_count": cache_hit_count,
        "cache_miss_count": cache_miss_count,
        "validation_logs": [_serialize_history_record(record) for record in records[:limit]],
        "recent_failures": recent_failures,
    }


def _serialize_failure_record(record: QueryHistory) -> dict[str, Any]:
    return {
        "natural_language_query": record.natural_language_query,
        "generated_sql": record.generated_sql,
        "validation_status": record.validation_status,
        "failure_type": "Schema Mismatch" if _is_schema_mismatch(record) else "Validation Failure",
        "created_at": record.created_at.isoformat(),
    }


def _is_valid(validation_status: str) -> bool:
    return validation_status.lower() == "valid"


def _is_schema_mismatch(record: QueryHistory) -> bool:
    return record.generated_sql.strip() == "SCHEMA_MISMATCH"
