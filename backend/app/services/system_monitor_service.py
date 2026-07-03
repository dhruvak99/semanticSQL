from collections import Counter
from typing import Any

from sqlalchemy import desc, select

from app.db.session import SessionLocal
from app.models.query_history import QueryHistory
from app.services.query_history_service import _serialize_history_record, normalize_generation_mode


def get_system_monitor_metrics(limit: int = 10) -> dict[str, Any]:
    with SessionLocal() as session:
        records = session.execute(
            select(QueryHistory).order_by(QueryHistory.created_at.asc(), QueryHistory.id.asc())
        ).scalars().all()
        recent_records = session.execute(
            select(QueryHistory)
            .order_by(desc(QueryHistory.created_at), desc(QueryHistory.id))
            .limit(limit)
        ).scalars().all()
        recent_failure_records = session.execute(
            select(QueryHistory)
            .where(QueryHistory.validation_status.ilike("invalid"))
            .order_by(desc(QueryHistory.created_at), desc(QueryHistory.id))
            .limit(limit)
        ).scalars().all()

    total_queries = len(records)
    successful_queries = sum(1 for record in records if _is_valid(record.validation_status))
    failed_queries = total_queries - successful_queries
    cache_hits = sum(1 for record in records if record.cache_status.lower() == "hit")
    cache_misses = total_queries - cache_hits
    llm_queries = sum(1 for record in records if normalize_generation_mode(record.generation_mode) == "LLM")
    rule_queries = sum(1 for record in records if normalize_generation_mode(record.generation_mode) == "Rule")
    schema_mismatches = sum(1 for record in records if _is_schema_mismatch(record.generated_sql))
    average_execution_time = (
        sum(record.execution_time for record in records) / total_queries
        if total_queries
        else 0.0
    )
    cache_hit_rate = (cache_hits / total_queries) * 100 if total_queries else 0.0
    volume_by_date = Counter(record.created_at.date().isoformat() for record in records)

    return {
        "total_queries": total_queries,
        "successful_queries": successful_queries,
        "failed_queries": failed_queries,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_hit_rate": round(cache_hit_rate, 1),
        "average_execution_time": round(average_execution_time, 3),
        "schema_mismatches": schema_mismatches,
        "llm_queries": llm_queries,
        "rule_queries": rule_queries,
        "recent_failures": [_serialize_failure(record) for record in recent_failure_records],
        "recent_activity": [_serialize_history_record(record) for record in recent_records],
        "query_volume_trend": [
            {"date": date, "count": count}
            for date, count in sorted(volume_by_date.items())
        ],
    }


def _serialize_failure(record: QueryHistory) -> dict[str, Any]:
    return {
        "natural_language_query": record.natural_language_query,
        "generated_sql": record.generated_sql,
        "failure_type": "Schema Mismatch" if _is_schema_mismatch(record.generated_sql) else "Validation Failure",
        "created_at": record.created_at.isoformat(),
    }


def _is_valid(validation_status: str) -> bool:
    return validation_status.lower() == "valid"


def _is_schema_mismatch(generated_sql: str) -> bool:
    return generated_sql.strip() == "SCHEMA_MISMATCH"
