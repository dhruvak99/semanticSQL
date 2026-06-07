import logging
import time

from app.schemas.query import QueryProcessResponse
from app.services.database_service import DatabaseServiceError, execute_query
from app.services.sql_generation_service import QueryType, generate_sql

logger = logging.getLogger(__name__)


def process_semantic_query(query: str) -> QueryProcessResponse:
    start_time = time.perf_counter()
    cache_hit = _mock_semantic_cache_check(query)
    generation_result = generate_sql(query)
    validation_status = "invalid" if generation_result.query_type == QueryType.UNKNOWN else "valid"

    logger.info("Input Query: %s", query)
    logger.info("Generated SQL: %s", generation_result.sql)
    logger.info("Query Type: %s", generation_result.query_type.value)

    try:
        results = execute_query(generation_result.sql) if validation_status == "valid" else []
    except DatabaseServiceError:
        execution_time = round(time.perf_counter() - start_time, 4)
        logger.info("Execution Time: %.4f sec", execution_time)
        logger.info("Rows Returned: 0")
        raise

    execution_time = round(time.perf_counter() - start_time, 4)

    logger.info("Execution Time: %.4f sec", execution_time)
    logger.info("Rows Returned: %s", len(results))

    # Mocked stages: semantic cache, validation, and auto correction.
    return QueryProcessResponse(
        generated_sql=generation_result.sql,
        cache_hit=cache_hit,
        validation_status=validation_status,
        execution_time=execution_time,
        rows_returned=len(results),
        results=results,
    )


def _mock_semantic_cache_check(query: str) -> bool:
    normalized_query = query.lower()
    return "department" in normalized_query and "finance" in normalized_query
