import logging
import time

from app.schemas.query import QueryProcessResponse
from app.services.database_service import DatabaseServiceError, execute_query
from app.services.llm_sql_generation_service import SCHEMA_MISMATCH, generate_sql as generate_sql_with_llm
from app.services.query_history_service import create_history_record, normalize_generation_mode
from app.services.semantic_cache_service import get_semantic_cache_service
from app.services.sql_generation_service import QueryType, generate_sql as generate_sql_with_rules
from app.services.sql_validation_service import validate_sql

logger = logging.getLogger(__name__)


def process_semantic_query(query: str) -> QueryProcessResponse:
    start_time = time.perf_counter()
    semantic_cache = get_semantic_cache_service()

    embedding_start_time = time.perf_counter()
    query_embedding = semantic_cache.generate_embedding(query)
    embedding_time = time.perf_counter() - embedding_start_time

    cache_search_start_time = time.perf_counter()
    cache_result = semantic_cache.search(query_embedding)
    cache_search_time = time.perf_counter() - cache_search_start_time
    logger.info("Timing: embedding generation stage %.4f sec", embedding_time)
    logger.info("Timing: similarity search stage %.4f sec", cache_search_time)
    logger.info("Semantic cache %s", "hit" if cache_result.hit else "miss")

    if cache_result.hit and cache_result.entry is not None:
        cached_payload = cache_result.entry.response_payload
        execution_time = round(time.perf_counter() - start_time, 4)
        generation_mode = _format_generation_mode(str(cached_payload.get("generation_mode", "Rule")))
        logger.info("Timing: cache retrieval stage %.4f sec", execution_time)
        logger.info("Timing: SQL generation skipped on cache hit")
        logger.info("Timing: validation skipped on cache hit")
        logger.info("Timing: database execution skipped on cache hit")
        logger.info("Input Query: %s", query)
        logger.info("Generated SQL: %s", cache_result.entry.generated_sql)
        logger.info("Query Type: semantic_cache_hit")
        logger.info("Generation Mode: %s", generation_mode)
        logger.info("Execution Time: %.4f sec", execution_time)
        logger.info("Timing: total request %.4f sec", execution_time)
        logger.info("Rows Returned: %s", cached_payload["rows_returned"])
        response = QueryProcessResponse(
            generation_mode=generation_mode,
            generated_sql=str(cached_payload["generated_sql"]),
            cache_hit=True,
            similarity_score=cache_result.similarity_score,
            validation_status=str(cached_payload["validation_status"]),
            validation_errors=list(cached_payload.get("validation_errors", [])),  # type: ignore[arg-type]
            execution_time=execution_time,
            rows_returned=int(cached_payload["rows_returned"]),
            results=list(cached_payload["results"]),  # type: ignore[arg-type]
        )
        _record_history(query, response)
        return response

    rule_generation_start_time = time.perf_counter()
    rule_generation_result = generate_sql_with_rules(query)
    rule_generation_time = time.perf_counter() - rule_generation_start_time
    logger.info("Timing: rule generation %.4f sec", rule_generation_time)

    if rule_generation_result.query_type == QueryType.UNKNOWN:
        llm_generation_start_time = time.perf_counter()
        llm_generation_result = generate_sql_with_llm(query)
        llm_generation_time = time.perf_counter() - llm_generation_start_time
        generated_sql = llm_generation_result.sql
        generation_mode = _format_generation_mode(llm_generation_result.generation_mode)
        query_type = "llm_generated"
        logger.info("Timing: llm generation %.4f sec", llm_generation_time)
    else:
        generated_sql = rule_generation_result.sql
        generation_mode = _format_generation_mode("Rule")
        query_type = rule_generation_result.query_type.value
        logger.info("Timing: llm generation skipped; rule SQL generated")

    if generated_sql.strip() == SCHEMA_MISMATCH:
        execution_time = round(time.perf_counter() - start_time, 4)
        validation_errors = ["Requested table or column does not exist in the current schema."]
        logger.info("Input Query: %s", query)
        logger.info("Generated SQL: %s", generated_sql)
        logger.info("Query Type: %s", query_type)
        logger.info("Generation Mode: %s", generation_mode)
        logger.info("Validation Errors: %s", validation_errors)
        logger.info("Timing: validation skipped due to schema mismatch sentinel")
        logger.info("Timing: database execution skipped due to schema mismatch sentinel")
        logger.info("Timing: semantic cache store skipped due to schema mismatch sentinel")
        logger.info("Execution Time: %.4f sec", execution_time)
        logger.info("Timing: total request %.4f sec", execution_time)
        logger.info("Rows Returned: 0")
        response = QueryProcessResponse(
            generation_mode=generation_mode,
            generated_sql=generated_sql,
            cache_hit=False,
            similarity_score=cache_result.similarity_score,
            validation_status="invalid",
            validation_errors=validation_errors,
            execution_time=execution_time,
            rows_returned=0,
            results=[],
        )
        _record_history(query, response)
        return response

    validation_start_time = time.perf_counter()
    validation_result = validate_sql(generated_sql)
    validation_status = "valid" if validation_result.valid else "invalid"
    logger.info("Timing: validation %.4f sec", time.perf_counter() - validation_start_time)

    logger.info("Input Query: %s", query)
    logger.info("Generated SQL: %s", generated_sql)
    logger.info("Query Type: %s", query_type)
    logger.info("Generation Mode: %s", generation_mode)

    if not validation_result.valid:
        execution_time = round(time.perf_counter() - start_time, 4)
        logger.info("Validation Errors: %s", validation_result.errors)
        logger.info("Timing: database execution skipped due to validation failure")
        logger.info("Execution Time: %.4f sec", execution_time)
        logger.info("Timing: total request %.4f sec", execution_time)
        logger.info("Rows Returned: 0")

        response = QueryProcessResponse(
            generation_mode=generation_mode,
            generated_sql=generated_sql,
            cache_hit=False,
            similarity_score=cache_result.similarity_score,
            validation_status=validation_status,
            validation_errors=validation_result.errors,
            execution_time=execution_time,
            rows_returned=0,
            results=[],
        )
        semantic_cache.store(
            query=query,
            embedding=query_embedding,
            generated_sql=generated_sql,
            response_payload=response.model_dump(),
        )
        _record_history(query, response)
        return response

    try:
        database_start_time = time.perf_counter()
        results = execute_query(generated_sql)
        logger.info("Timing: database execution %.4f sec", time.perf_counter() - database_start_time)
    except DatabaseServiceError:
        execution_time = round(time.perf_counter() - start_time, 4)
        logger.info("Timing: database execution %.4f sec", time.perf_counter() - database_start_time)
        logger.info("Execution Time: %.4f sec", execution_time)
        logger.info("Timing: total request %.4f sec", execution_time)
        logger.info("Rows Returned: 0")
        raise

    execution_time = round(time.perf_counter() - start_time, 4)

    logger.info("Execution Time: %.4f sec", execution_time)
    logger.info("Timing: total request %.4f sec", execution_time)
    logger.info("Rows Returned: %s", len(results))

    # Mocked stage: auto correction.
    response = QueryProcessResponse(
        generation_mode=generation_mode,
        generated_sql=generated_sql,
        cache_hit=False,
        similarity_score=cache_result.similarity_score,
        validation_status=validation_status,
        validation_errors=validation_result.errors,
        execution_time=execution_time,
        rows_returned=len(results),
        results=results,
    )
    semantic_cache.store(
        query=query,
        embedding=query_embedding,
        generated_sql=generated_sql,
        response_payload=response.model_dump(),
    )
    _record_history(query, response)
    return response


def _record_history(query: str, response: QueryProcessResponse) -> None:
    create_history_record(
        natural_language_query=query,
        generated_sql=response.generated_sql,
        generation_mode=_format_generation_mode(response.generation_mode),
        cache_status="Hit" if response.cache_hit else "Miss",
        validation_status=response.validation_status.capitalize(),
        execution_time=response.execution_time,
        rows_returned=response.rows_returned,
    )


def _format_generation_mode(generation_mode: str) -> str:
    return normalize_generation_mode(generation_mode)
