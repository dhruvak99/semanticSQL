import logging
import re
import time
from dataclasses import dataclass
from difflib import SequenceMatcher

import requests
from requests import RequestException
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine
from app.services.model_runtime_state import get_active_model

logger = logging.getLogger(__name__)

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
SCHEMA_MATCH_THRESHOLD = 0.86
STOPWORDS = {
    "a",
    "above",
    "all",
    "an",
    "and",
    "are",
    "ascending",
    "at",
    "average",
    "avg",
    "below",
    "by",
    "count",
    "descending",
    "each",
    "equal",
    "equals",
    "find",
    "first",
    "for",
    "from",
    "get",
    "group",
    "greater",
    "has",
    "have",
    "higher",
    "highest",
    "in",
    "is",
    "least",
    "less",
    "list",
    "lower",
    "lowest",
    "maximum",
    "max",
    "minimum",
    "min",
    "more",
    "most",
    "of",
    "or",
    "order",
    "over",
    "show",
    "sort",
    "sum",
    "than",
    "the",
    "to",
    "top",
    "total",
    "under",
    "what",
    "where",
    "which",
    "whose",
    "with",
}
VALUE_PREFIXES = {"from", "in", "is", "equal", "equals"}


class LLMSQLGenerationError(Exception):
    pass


@dataclass(frozen=True)
class LLMSQLGenerationResult:
    sql: str
    generation_mode: str = "LLM"


def generate_sql(natural_language_query: str) -> LLMSQLGenerationResult:
    total_start_time = time.perf_counter()

    schema_start_time = time.perf_counter()
    schema = extract_schema()
    schema_context = build_schema_context(schema)
    schema_extraction_time = time.perf_counter() - schema_start_time

    grounding_result = _ground_query_to_schema(natural_language_query, schema)
    if not grounding_result.valid:
        total_generation_time = time.perf_counter() - total_start_time
        logger.info("Timing: LLM schema extraction %.4f sec", schema_extraction_time)
        logger.info("LLM schema grounding failed: %s", grounding_result.reason)
        logger.info("Generated LLM SQL: %s", SCHEMA_MISMATCH)
        logger.info("Timing: LLM SQL generation total %.4f sec", total_generation_time)
        return LLMSQLGenerationResult(sql=SCHEMA_MISMATCH)

    prompt = build_prompt(
        schema_context,
        grounding_result.query,
        grounding_result.context,
    )
    logger.info("Timing: LLM schema extraction %.4f sec", schema_extraction_time)
    logger.info("LLM prompt size: %s chars", len(prompt))

    llm_start_time = time.perf_counter()
    generated_sql = _call_ollama(prompt)
    llm_response_time = time.perf_counter() - llm_start_time

    total_generation_time = time.perf_counter() - total_start_time
    logger.info("Generated LLM SQL: %s", generated_sql)
    logger.info("Timing: LLM response %.4f sec", llm_response_time)
    logger.info("Timing: LLM SQL generation total %.4f sec", total_generation_time)

    return LLMSQLGenerationResult(sql=generated_sql)


def extract_schema_context() -> str:
    return build_schema_context(extract_schema())


def extract_schema() -> dict[str, dict[str, str]]:
    try:
        database_inspector = inspect(engine)
        table_names = sorted(database_inspector.get_table_names())
        return {
            table_name: {
                column["name"]: _normalize_column_type(column.get("type"))
                for column in database_inspector.get_columns(table_name)
            }
            for table_name in table_names
        }
    except SQLAlchemyError as error:
        logger.exception("Schema introspection failed")
        raise LLMSQLGenerationError("Unable to extract database schema.") from error


def build_schema_context(schema: dict[str, dict[str, str]]) -> str:
    table_blocks: list[str] = []
    for table_name, columns in sorted(schema.items()):
        column_lines = [
            f"{column_name} {column_type}"
            for column_name, column_type in columns.items()
        ]
        table_blocks.append(f"{table_name}(\n" + ",\n".join(column_lines) + "\n)")
    return "\n\n".join(table_blocks)


def build_prompt(schema_context: str, natural_language_query: str, grounding_context: str = "") -> str:
    resolved_context = f"\nResolved high-confidence schema matches:\n{grounding_context}\n" if grounding_context else ""
    return (
        "You are an expert SQL generation assistant.\n\n"
        "Generate only valid SQLite SQL or return SCHEMA_MISMATCH.\n\n"
        "Rules:\n\n"
        "* Return SQL only, or exactly SCHEMA_MISMATCH.\n"
        "* Do not explain.\n"
        "* Do not use markdown.\n"
        "* Use only tables and columns provided in the schema.\n"
        "* Never invent tables.\n"
        "* Never invent columns.\n\n"
        "* Minor spelling mistakes are allowed only when there is an obvious high-confidence schema match.\n"
        "* Semantic substitutions are forbidden. Do not map suppliers to products, customers to employees, or warehouses to projects.\n"
        "* If a requested table, entity, or column is not present in the schema, return exactly SCHEMA_MISMATCH.\n"
        "* If the request cannot be answered using only the provided schema, return exactly SCHEMA_MISMATCH.\n\n"
        "Schema:\n"
        f"{schema_context}\n\n"
        f"{resolved_context}"
        "User Request:\n"
        f"{natural_language_query}\n\n"
        "SQL:"
    )


def _call_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_GENERATE_URL,
            json={
                "model": get_active_model(),
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
    except RequestException as error:
        logger.exception("Ollama SQL generation request failed")
        raise LLMSQLGenerationError("Ollama SQL generation request failed.") from error

    payload = response.json()
    generated_sql = _clean_generated_sql(str(payload.get("response", "")))
    if not generated_sql:
        raise LLMSQLGenerationError("Ollama returned an empty SQL response.")

    return generated_sql


def _clean_generated_sql(generated_text: str) -> str:
    cleaned = generated_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```sql").removeprefix("```").strip()
    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()
    return cleaned


def _normalize_column_type(column_type: object) -> str:
    return str(column_type).upper()


@dataclass(frozen=True)
class _GroundingResult:
    valid: bool
    query: str
    context: str
    reason: str = ""


def _ground_query_to_schema(natural_language_query: str, schema: dict[str, dict[str, str]]) -> _GroundingResult:
    tokens = _extract_tokens(natural_language_query.lower())
    table_matches = _find_schema_matches(tokens, _table_terms(schema))
    column_matches = _find_schema_matches(tokens, _column_terms(schema))

    if not table_matches and not column_matches:
        return _GroundingResult(
            valid=False,
            query=natural_language_query,
            context="",
            reason="No requested table or column matched the active schema.",
        )

    value_tokens = _value_tokens(tokens)
    unmatched_schema_like_tokens = [
        token
        for token in tokens
        if token not in STOPWORDS
        and not token.isnumeric()
        and token not in table_matches
        and token not in column_matches
        and token not in value_tokens
    ]
    if unmatched_schema_like_tokens:
        return _GroundingResult(
            valid=False,
            query=natural_language_query,
            context="",
            reason=f"Unmatched schema terms: {', '.join(unmatched_schema_like_tokens)}",
        )

    grounded_query = natural_language_query
    context_lines: list[str] = []
    replacements = {**column_matches, **table_matches}
    for requested_term, schema_term in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        if requested_term != schema_term:
            grounded_query = re.sub(
                rf"\b{re.escape(requested_term)}\b",
                schema_term,
                grounded_query,
                flags=re.IGNORECASE,
            )
            context_lines.append(f"{requested_term} -> {schema_term}")

    return _GroundingResult(
        valid=True,
        query=grounded_query,
        context="\n".join(context_lines),
    )


def _extract_tokens(query: str) -> list[str]:
    return re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", query)


def _find_schema_matches(tokens: list[str], terms: dict[str, str]) -> dict[str, str]:
    matches: dict[str, str] = {}
    for token in tokens:
        normalized_token = _singularize(token)
        alias_token = _schema_alias(normalized_token, terms)
        if alias_token:
            matches[token] = terms[alias_token]
            continue
        if token in terms:
            matches[token] = terms[token]
            continue
        if normalized_token in terms:
            matches[token] = terms[normalized_token]
            continue

        best_term, best_score = _best_fuzzy_match(normalized_token, terms)
        if best_term and best_score >= SCHEMA_MATCH_THRESHOLD:
            matches[token] = terms[best_term]
    return matches


def _value_tokens(tokens: list[str]) -> set[str]:
    values: set[str] = set()
    for index, token in enumerate(tokens):
        previous_token = tokens[index - 1] if index > 0 else ""
        if previous_token in VALUE_PREFIXES:
            values.add(token)
    return values


def _schema_alias(token: str, terms: dict[str, str]) -> str | None:
    aliases = {
        "rated": "rating",
        "rate": "rating",
    }
    alias = aliases.get(token)
    return alias if alias in terms else None


def _table_terms(schema: dict[str, dict[str, str]]) -> dict[str, str]:
    terms: dict[str, str] = {}
    for table_name in schema:
        terms[table_name.lower()] = table_name
        terms[_singularize(table_name.lower())] = table_name
    return terms


def _column_terms(schema: dict[str, dict[str, str]]) -> dict[str, str]:
    terms: dict[str, str] = {}
    for columns in schema.values():
        for column_name in columns:
            normalized_column = column_name.lower()
            terms[normalized_column] = column_name
            terms[_singularize(normalized_column)] = column_name
            for part in normalized_column.split("_"):
                if len(part) > 2:
                    terms[part] = column_name
                    terms[_singularize(part)] = column_name
    return terms


def _best_fuzzy_match(token: str, terms: dict[str, str]) -> tuple[str | None, float]:
    best_term: str | None = None
    best_score = 0.0
    for term in terms:
        if len(token) < 4 or len(term) < 4:
            continue
        score = SequenceMatcher(None, token, term).ratio()
        if score > best_score:
            best_term = term
            best_score = score
    return best_term, best_score


def _singularize(value: str) -> str:
    if value.endswith("ies") and len(value) > 3:
        return f"{value[:-3]}y"
    if value.endswith("s") and len(value) > 3:
        return value[:-1]
    return value
