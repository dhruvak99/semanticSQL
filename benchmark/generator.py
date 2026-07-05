from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

import requests
import sqlglot
from sqlglot import exp

from benchmark.adapters import ColumnInfo, ForeignKeyInfo, SQLiteAdapter, TableInfo
from benchmark.adapters.base import SchemaInfo
from benchmark.validation import validate_sql_against_schema

BENCHMARK_NAME = "SemanticSQL Benchmark"
BENCHMARK_VERSION = "1.0.0"
FUNCTIONAL_COUNT = 300
SEMANTIC_VARIANTS_PER_FUNCTIONAL = 5
INVALID_COUNT = 100

BASE_CATEGORY_REQUIREMENTS = {
    "SELECT": 15,
    "WHERE": 20,
    "ORDER_BY": 15,
    "LIMIT": 15,
    "DISTINCT": 15,
    "COUNT": 25,
    "AVG": 20,
    "MIN": 15,
    "MAX": 15,
    "SUM": 15,
    "GROUP_BY": 25,
    "HAVING": 20,
    "JOIN": 30,
    "NESTED": 25,
    "IN": 15,
    "EXISTS": 15,
}

BASE_CATEGORY_DIFFICULTY_PLAN = {
    "SELECT": ("easy", 15),
    "WHERE": ("easy", 20),
    "ORDER_BY": ("easy", 15),
    "LIMIT": ("easy", 15),
    "DISTINCT": ("easy", 15),
    "COUNT": ("easy", 25),
    "AVG": ("medium", 20),
    "MIN": ("medium", 15),
    "MAX": ("medium", 15),
    "SUM": ("medium", 15),
    "GROUP_BY": ("medium", 25),
    "NESTED": ("medium", 25),
    "JOIN": (("medium", 5), ("hard", 25)),
    "HAVING": ("hard", 20),
    "IN": ("hard", 15),
    "EXISTS": ("hard", 15),
}

BASE_DIFFICULTY_TARGETS = {
    "easy": 105,
    "medium": 120,
    "hard": 75,
}

PARAPHRASE_CACHE_PATH = Path("benchmark/paraphrase_cache.json")
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
COMPARISON_WORDS = ("at least", "greater than", "above", "below", "less than", "no lower than")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the SemanticSQL benchmark datasets.")
    parser.add_argument("--database-url", help="SQLAlchemy database URL. Defaults to backend/semanticsql.db.")
    parser.add_argument("--output-dir", default="benchmark", help="Directory where benchmark files are written.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    adapter = SQLiteAdapter(database_url=args.database_url)
    schema = adapter.introspect()
    category_plan = _allocate_schema_aware_category_plan(schema)
    functional_queries = _generate_functional_queries(schema, category_plan)
    category_requirements = _category_requirements_from_queries(functional_queries)
    difficulty_targets = _difficulty_targets_from_queries(functional_queries)
    _validate_no_duplicates("functional queries", functional_queries)
    semantic_queries = _generate_semantic_queries(functional_queries)
    _validate_no_duplicates("semantic queries", semantic_queries)
    invalid_queries = _generate_invalid_queries(schema)
    _validate_no_duplicates("invalid queries", invalid_queries)

    consistency = _validate_benchmark(
        schema,
        functional_queries,
        semantic_queries,
        invalid_queries,
        category_requirements,
        difficulty_targets,
    )
    coverage = _analyze_schema_coverage(schema, functional_queries)
    statistics = _build_statistics(functional_queries, semantic_queries, invalid_queries)
    quality = _build_quality_report(coverage, statistics, consistency, category_requirements)
    paraphrase_audit = _build_paraphrase_audit(functional_queries, semantic_queries, coverage, quality)
    _write_benchmark_files(
        output_dir,
        schema,
        functional_queries,
        semantic_queries,
        invalid_queries,
        coverage,
        statistics,
        quality,
        consistency,
        paraphrase_audit,
        category_requirements,
        difficulty_targets,
    )


def _allocate_schema_aware_category_plan(schema: SchemaInfo) -> dict[str, list[tuple[str, int]]]:
    capacities = _estimate_category_capacities(schema)
    plan: dict[str, list[tuple[str, int]]] = {}
    overflow_by_difficulty: Counter[str] = Counter()

    for category, requested_plan in BASE_CATEGORY_DIFFICULTY_PLAN.items():
        entries = _plan_entries(requested_plan)
        category_capacity = capacities.get(category, 0)
        allocated_for_category = 0
        for difficulty, requested_count in entries:
            available = max(0, category_capacity - allocated_for_category)
            accepted = min(requested_count, available)
            if accepted:
                plan.setdefault(category, []).append((difficulty, accepted))
                allocated_for_category += accepted
            if accepted < requested_count:
                overflow_by_difficulty[difficulty] += requested_count - accepted

    for difficulty in ("hard", "medium", "easy"):
        remaining = overflow_by_difficulty[difficulty]
        while remaining > 0:
            category = _next_redistribution_category(plan, capacities, difficulty)
            if category is None and difficulty == "hard":
                category = _next_redistribution_category(plan, capacities, "medium")
            if category is None:
                category = _next_redistribution_category(plan, capacities, difficulty)
            if category is None:
                raise ValueError(f"Schema cannot support {FUNCTIONAL_COUNT} unique functional queries.")

            assigned_difficulty = _difficulty_for_category(category, difficulty)
            _increment_plan_count(plan, category, assigned_difficulty)
            remaining -= 1

    allocated_total = sum(count for entries in plan.values() for _, count in entries)
    if allocated_total != FUNCTIONAL_COUNT:
        raise ValueError(f"Expected {FUNCTIONAL_COUNT} allocated functional queries, got {allocated_total}.")

    return {category: entries for category, entries in plan.items() if sum(count for _, count in entries)}


def _estimate_category_capacities(schema: SchemaInfo) -> dict[str, int]:
    table_count = max(1, len(schema.tables))
    column_count = max(1, sum(len(table.columns) for table in schema.tables))
    numeric_count = max(1, sum(1 for table in schema.tables for column in table.columns if _is_numeric(column) and not column.primary_key))
    text_count = max(1, sum(1 for table in schema.tables for column in table.columns if _is_text(column)))
    foreign_key_count = len(schema.foreign_keys)
    chain_count = sum(1 for relation in schema.foreign_keys if len(_relationship_chain(schema, relation)) >= 2)

    return {
        "SELECT": table_count * column_count * 8,
        "WHERE": column_count * 80,
        "ORDER_BY": column_count * 50,
        "LIMIT": table_count * 80,
        "DISTINCT": (text_count + column_count) * 40,
        "COUNT": column_count * 80,
        "AVG": numeric_count * 60,
        "MIN": numeric_count * 60,
        "MAX": numeric_count * 60,
        "SUM": numeric_count * 60,
        "GROUP_BY": (text_count + column_count) * 50,
        "HAVING": (text_count + column_count) * 80,
        "JOIN": max(0, foreign_key_count * 80 + chain_count * 120),
        "NESTED": column_count * 80 + max(0, foreign_key_count * 60),
        "IN": column_count * 80,
        "EXISTS": max(0, foreign_key_count * 60),
    }


def _plan_entries(plan: tuple[Any, ...] | tuple[str, int]) -> list[tuple[str, int]]:
    if isinstance(plan[0], tuple):
        return [(str(difficulty), int(count)) for difficulty, count in plan]  # type: ignore[misc]
    difficulty, count = plan
    return [(str(difficulty), int(count))]


def _category_requirements_from_plan(plan: dict[str, list[tuple[str, int]]]) -> dict[str, int]:
    return {category: sum(count for _, count in entries) for category, entries in sorted(plan.items())}


def _difficulty_targets_from_plan(plan: dict[str, list[tuple[str, int]]]) -> dict[str, int]:
    targets: Counter[str] = Counter()
    for entries in plan.values():
        for difficulty, count in entries:
            targets[difficulty] += count
    return dict(sorted(targets.items()))


def _category_requirements_from_queries(functional_queries: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(query["category"] for query in functional_queries).items()))


def _difficulty_targets_from_queries(functional_queries: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(query["difficulty"] for query in functional_queries).items()))


def _next_redistribution_category(
    plan: dict[str, list[tuple[str, int]]],
    capacities: dict[str, int],
    difficulty: str,
) -> str | None:
    candidates = [
        category
        for category in _redistribution_order(difficulty)
        if _allocated_category_count(plan, category) < capacities.get(category, 0)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda category: (_allocated_category_count(plan, category), category))


def _redistribution_order(difficulty: str) -> tuple[str, ...]:
    if difficulty == "hard":
        return ("JOIN", "HAVING", "IN", "NESTED", "EXISTS")
    if difficulty == "medium":
        return ("GROUP_BY", "AVG", "MIN", "MAX", "SUM", "NESTED", "JOIN")
    return ("WHERE", "COUNT", "ORDER_BY", "LIMIT", "DISTINCT", "SELECT")


def _difficulty_for_category(category: str, requested_difficulty: str) -> str:
    if category == "JOIN" and requested_difficulty == "hard":
        return "hard"
    if category == "NESTED" and requested_difficulty == "hard":
        return "hard"
    if category in {"HAVING", "IN", "EXISTS"}:
        return "hard"
    if category in {"AVG", "MIN", "MAX", "SUM", "GROUP_BY", "NESTED", "JOIN"}:
        return "medium"
    return "easy"


def _increment_plan_count(plan: dict[str, list[tuple[str, int]]], category: str, difficulty: str) -> None:
    entries = plan.setdefault(category, [])
    for index, (entry_difficulty, count) in enumerate(entries):
        if entry_difficulty == difficulty:
            entries[index] = (entry_difficulty, count + 1)
            return
    entries.append((difficulty, 1))


def _allocated_category_count(plan: dict[str, list[tuple[str, int]]], category: str) -> int:
    return sum(count for _, count in plan.get(category, []))


def _generate_functional_queries(schema: SchemaInfo, category_plan: dict[str, list[tuple[str, int]]]) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    category_offsets: Counter[str] = Counter()
    functional_nl_seen: set[str] = set()
    functional_sql_seen: set[str] = set()
    shortfalls: Counter[str] = Counter()

    for category, entries in category_plan.items():
        for difficulty, count in entries:
            accepted = 0
            attempts = 0
            max_attempts = max(500, count * 200)
            while accepted < count:
                query = _build_functional_query(schema, category, difficulty, category_offsets[category])
                category_offsets[category] += 1
                attempts += 1
                if not _is_unique_functional_candidate(query, functional_nl_seen, functional_sql_seen):
                    if attempts > max_attempts:
                        shortfalls[difficulty] += count - accepted
                        break
                    continue
                _append_functional_query(queries, query)
                functional_nl_seen.add(query["natural_language_query"])
                functional_sql_seen.add(query["expected_sql"])
                accepted += 1
            if accepted < count:
                continue

    for difficulty in ("hard", "medium", "easy"):
        remaining = shortfalls[difficulty]
        while remaining > 0:
            if not _append_replacement_functional_query(
                schema,
                queries,
                functional_nl_seen,
                functional_sql_seen,
                category_offsets,
                difficulty,
            ):
                break
            remaining -= 1

    while len(queries) < FUNCTIONAL_COUNT:
        if not _append_replacement_functional_query(
            schema,
            queries,
            functional_nl_seen,
            functional_sql_seen,
            category_offsets,
            "hard",
        ):
            if not _append_replacement_functional_query(
                schema,
                queries,
                functional_nl_seen,
                functional_sql_seen,
                category_offsets,
                "medium",
            ):
                if not _append_replacement_functional_query(
                    schema,
                    queries,
                    functional_nl_seen,
                    functional_sql_seen,
                    category_offsets,
                    "easy",
                ):
                    raise ValueError(f"Schema cannot support {FUNCTIONAL_COUNT} unique functional queries.")

    return queries


def _is_unique_functional_candidate(query: dict[str, Any], nl_seen: set[str], sql_seen: set[str]) -> bool:
    return query["natural_language_query"] not in nl_seen and query["expected_sql"] not in sql_seen


def _append_replacement_functional_query(
    schema: SchemaInfo,
    queries: list[dict[str, Any]],
    nl_seen: set[str],
    sql_seen: set[str],
    category_offsets: Counter[str],
    requested_difficulty: str,
) -> bool:
    for category in _redistribution_order(requested_difficulty):
        difficulty = _difficulty_for_category(category, requested_difficulty)
        if category in {"JOIN", "EXISTS"} and not schema.foreign_keys:
            continue
        for _ in range(500):
            query = _build_functional_query(schema, category, difficulty, category_offsets[category])
            category_offsets[category] += 1
            if not _is_unique_functional_candidate(query, nl_seen, sql_seen):
                continue
            _append_functional_query(queries, query)
            nl_seen.add(query["natural_language_query"])
            sql_seen.add(query["expected_sql"])
            return True
    return False


def _append_functional_query(queries: list[dict[str, Any]], query: dict[str, Any]) -> None:
    query["id"] = f"F{len(queries) + 1:04d}"
    query["benchmark_version"] = BENCHMARK_VERSION
    query["dataset"] = "functional"
    queries.append(query)


def _build_functional_query(schema: SchemaInfo, category: str, difficulty: str, index: int) -> dict[str, Any]:
    table = _table_at(schema, index)
    text_column = _text_column(table, index)
    numeric_column = _numeric_column(table, index)
    any_column = _column_at(table, index)
    primary_key = table.primary_keys[index % len(table.primary_keys)] if table.primary_keys else any_column.name
    relation = _relation_at(schema, index)
    projection = _projection(table, index)

    if category == "SELECT":
        sql = f"SELECT {', '.join(projection)} FROM {table.name};"
        return _record(category, difficulty, _nl_select(table, projection, index), sql, [table.name], projection)

    if category == "WHERE":
        column = numeric_column or text_column or any_column
        predicate = _predicate(column, index)
        sql = f"SELECT {', '.join(projection)} FROM {table.name} WHERE {predicate};"
        return _record(category, difficulty, _nl_where(table, column, index), sql, [table.name], _unique([*projection, column.name]))

    if category == "ORDER_BY":
        direction = "DESC" if index % 2 else "ASC"
        sql = f"SELECT {', '.join(projection)} FROM {table.name} ORDER BY {any_column.name} {direction} LIMIT {5 + index};"
        return _record(category, difficulty, _nl_order(table, any_column, direction, index), sql, [table.name], _unique([*projection, any_column.name]))

    if category == "LIMIT":
        limit = 3 + (index % 5)
        offset = index % 4
        sql = f"SELECT {', '.join(projection)} FROM {table.name} LIMIT {limit} OFFSET {offset};"
        return _record(category, difficulty, _nl_limit(table, limit, index), sql, [table.name], projection)

    if category == "DISTINCT":
        column = text_column or any_column
        sql = (
            f"SELECT DISTINCT {column.name} FROM {table.name} "
            f"WHERE {_predicate(column, index)} ORDER BY {column.name} ASC;"
        )
        return _record(category, difficulty, _nl_distinct(table, column, index), sql, [table.name], [column.name])

    if category == "COUNT":
        column = _column_at(table, index)
        sql = f"SELECT COUNT(*) AS row_count FROM {table.name} WHERE {_predicate(column, index)};"
        columns = [column.name]
        return _record(category, difficulty, _nl_count(table, column, index), sql, [table.name], columns)

    if category in {"AVG", "MIN", "MAX", "SUM"}:
        column = numeric_column or _numeric_column(_first_table_with_numeric(schema), index)
        table = _table_containing(schema, column.name, preferred=table)
        aggregate_filter = _aggregate_filter(table, column, index)
        sql = f"SELECT {category}({column.name}) AS {category.lower()}_{column.name} FROM {table.name}{aggregate_filter};"
        return _record(category, difficulty, _nl_aggregate(category, table, column, index), sql, [table.name], [column.name])

    if category == "GROUP_BY":
        group_column = text_column or any_column
        sql = (
            f"SELECT {group_column.name}, COUNT(*) AS row_count FROM {table.name} "
            f"WHERE {_predicate(group_column, index)} GROUP BY {group_column.name} ORDER BY COUNT(*) DESC;"
        )
        return _record(category, difficulty, _nl_group_by(table, group_column, index), sql, [table.name], [group_column.name])

    if category == "HAVING":
        group_column = text_column or any_column
        sql = (
            f"SELECT {group_column.name}, COUNT(*) AS row_count FROM {table.name} "
            f"WHERE {_predicate(group_column, index)} "
            f"GROUP BY {group_column.name} HAVING COUNT(*) > {index} ORDER BY COUNT(*) DESC;"
        )
        return _record(category, difficulty, _nl_having(table, group_column, index), sql, [table.name], [group_column.name])

    if category == "JOIN":
        return _join_query(schema, relation, index, difficulty)

    if category == "NESTED":
        if difficulty == "hard" and relation:
            source, target = _relation_tables(schema, relation)
            source_pk = source.primary_keys[0] if source.primary_keys else _column_at(source, index).name
            sql = (
                f"SELECT * FROM {source.name} WHERE {source_pk} IN "
                f"(SELECT {source_pk} FROM {source.name} WHERE {relation.source_column} IN "
                f"(SELECT {relation.target_column} FROM {target.name} WHERE {relation.target_column} IS NOT NULL) "
                f"GROUP BY {source_pk} HAVING COUNT(*) >= 1);"
            )
            return _record(category, difficulty, _nl_nested(source, target, index), sql, [source.name, target.name], [source_pk, relation.source_column, relation.target_column])
        filter_column = numeric_column or any_column
        if difficulty == "hard":
            sql = (
                f"SELECT * FROM {table.name} WHERE {primary_key} IN "
                f"(SELECT {primary_key} FROM {table.name} WHERE {_predicate(filter_column, index)} "
                f"GROUP BY {primary_key} HAVING COUNT(*) >= 1);"
            )
        else:
            sql = f"SELECT * FROM {table.name} WHERE {primary_key} IN (SELECT {primary_key} FROM {table.name} WHERE {_predicate(filter_column, index)});"
        return _record(category, difficulty, _nl_nested_self(table, filter_column, index), sql, [table.name], [primary_key, filter_column.name])

    if category == "IN":
        filter_column = numeric_column or any_column
        sql = (
            f"SELECT * FROM {table.name} WHERE {primary_key} IN "
            f"(SELECT {primary_key} FROM {table.name} WHERE {_predicate(filter_column, index)} "
            f"GROUP BY {primary_key} HAVING COUNT(*) >= 1);"
        )
        return _record(category, difficulty, _nl_in(table, primary_key, filter_column, index), sql, [table.name], [primary_key, filter_column.name])

    if category == "EXISTS" and relation:
        source, target = _relation_tables(schema, relation)
        sql = (
            f"SELECT * FROM {source.name} WHERE EXISTS (SELECT 1 FROM {target.name} "
            f"WHERE {source.name}.{relation.source_column} = {target.name}.{relation.target_column} "
            f"AND {target.name}.{relation.target_column} IS NOT NULL "
            f"AND {source.name}.{relation.source_column} IS NOT NULL LIMIT {1 + index});"
        )
        return _record(category, difficulty, _nl_exists(source, target, index), sql, [source.name, target.name], [relation.source_column, relation.target_column])

    raise ValueError(f"Unsupported category: {category}")


def _join_query(schema: SchemaInfo, relation: ForeignKeyInfo | None, index: int, difficulty: str) -> dict[str, Any]:
    if relation is None:
        table = _table_at(schema, index)
        return _build_functional_query(schema, "NESTED", difficulty, index)

    chain = _relationship_chain(schema, relation)
    if len(chain) >= 2 and index % 3 == 0:
        first, second = chain[0], chain[1]
        source, middle = _relation_tables(schema, first)
        _, target = _relation_tables(schema, second)
        sql = (
            f"SELECT {source.name}.*, {target.name}.{second.target_column} FROM {source.name} "
            f"JOIN {middle.name} ON {source.name}.{first.source_column} = {middle.name}.{first.target_column} "
            f"JOIN {target.name} ON {middle.name}.{second.source_column} = {target.name}.{second.target_column} "
            f"WHERE {source.name}.{first.source_column} IS NOT NULL "
            f"ORDER BY {source.name}.{first.source_column} ASC LIMIT {10 + index};"
        )
        return _record(
            "JOIN",
            difficulty,
            _nl_join_chain(source, middle, target, index),
            sql,
            [source.name, middle.name, target.name],
            [first.source_column, first.target_column, second.source_column, second.target_column],
            relationship_chain=[_fk_key(first), _fk_key(second)],
        )

    source, target = _relation_tables(schema, relation)
    if difficulty == "hard":
        sql = (
            f"SELECT {source.name}.*, {target.name}.{relation.target_column} FROM {source.name} "
            f"JOIN {target.name} ON {source.name}.{relation.source_column} = {target.name}.{relation.target_column} "
            f"WHERE EXISTS (SELECT 1 FROM {target.name} "
            f"WHERE {source.name}.{relation.source_column} = {target.name}.{relation.target_column} "
            f"AND {target.name}.{relation.target_column} IS NOT NULL) "
            f"ORDER BY {source.name}.{relation.source_column} ASC LIMIT {10 + index};"
        )
    else:
        sql = (
            f"SELECT {source.name}.*, {target.name}.{relation.target_column} FROM {source.name} "
            f"JOIN {target.name} ON {source.name}.{relation.source_column} = {target.name}.{relation.target_column} "
            f"WHERE {target.name}.{relation.target_column} IS NOT NULL "
            f"ORDER BY {source.name}.{relation.source_column} ASC LIMIT {10 + index};"
        )
    return _record(
        "JOIN",
        difficulty,
        _nl_join(source, target, index),
        sql,
        [source.name, target.name],
        [relation.source_column, relation.target_column],
        foreign_keys=[_fk_key(relation)],
    )


def _generate_semantic_queries(functional_queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paraphrase_cache = _load_paraphrase_cache()
    semantic_queries: list[dict[str, Any]] = []
    semantic_nl_seen: set[str] = set()
    semantic_sql_seen: set[str] = set()
    for functional_query in functional_queries:
        paraphrases = _paraphrases_for_functional_query(functional_query, paraphrase_cache, semantic_nl_seen)
        for paraphrase in paraphrases:
            semantic_queries.append(
                {
                    "id": f"S{len(semantic_queries) + 1:04d}",
                    "benchmark_version": BENCHMARK_VERSION,
                    "dataset": "semantic",
                    "functional_query_id": functional_query["id"],
                    "category": functional_query["category"],
                    "difficulty": functional_query["difficulty"],
                    "natural_language_query": paraphrase,
                    "expected_sql": functional_query["expected_sql"],
                    "tables": functional_query["tables"],
                    "columns": functional_query["columns"],
                    "complexity_score": functional_query["complexity_score"],
                }
            )
            semantic_nl_seen.add(paraphrase)
            semantic_sql_seen.add(functional_query["expected_sql"])
    _save_paraphrase_cache(paraphrase_cache)
    expected_count = len(functional_queries) * SEMANTIC_VARIANTS_PER_FUNCTIONAL
    if len(semantic_queries) != expected_count:
        raise ValueError(f"Expected {expected_count} semantic queries, generated {len(semantic_queries)}.")
    return semantic_queries


def _paraphrases_for_functional_query(
    functional_query: dict[str, Any],
    paraphrase_cache: dict[str, list[str]],
    semantic_nl_seen: set[str],
) -> list[str]:
    cache_key = f"{BENCHMARK_VERSION}:{functional_query['id']}:{functional_query['expected_sql']}"
    cached = paraphrase_cache.get(cache_key, [])
    if _valid_paraphrase_set(functional_query, cached):
        accepted_cached = [
            _clean_sentence(paraphrase)
            for paraphrase in cached
            if _clean_sentence(paraphrase) not in semantic_nl_seen
        ]
        if len(accepted_cached) >= SEMANTIC_VARIANTS_PER_FUNCTIONAL:
            return accepted_cached[:SEMANTIC_VARIANTS_PER_FUNCTIONAL]

    candidates = []
    if os.getenv("SEMANTICSQL_BENCHMARK_PARAPHRASE_MODE", "").lower() == "ollama":
        candidates.extend(_ollama_paraphrase_candidates(functional_query))
    candidates.extend(_rule_based_paraphrases(functional_query))
    candidates.extend(_deterministic_paraphrase_expansions(functional_query))

    accepted: list[str] = []
    for candidate in candidates:
        normalized = _clean_sentence(candidate)
        if normalized in semantic_nl_seen:
            continue
        if _is_valid_paraphrase(functional_query, normalized, accepted):
            accepted.append(normalized)
        if len(accepted) == SEMANTIC_VARIANTS_PER_FUNCTIONAL:
            break

    if len(accepted) != SEMANTIC_VARIANTS_PER_FUNCTIONAL:
        raise ValueError(f"Unable to generate enough paraphrases for {functional_query['id']}.")

    paraphrase_cache[cache_key] = accepted
    return accepted


def _rule_based_paraphrases(functional_query: dict[str, Any]) -> list[str]:
    subject = _semantic_subject(functional_query)
    category = functional_query["category"]
    table_label = _label(functional_query["tables"][0]) if functional_query["tables"] else "records"

    if category == "SELECT":
        return [
            f"List {subject}.",
            f"Display {subject}.",
            f"Which {subject} are stored?",
            f"Please show {subject}.",
            f"Return {subject}.",
            f"I'd like to see {subject}.",
        ]
    if category == "WHERE":
        return [
            f"Find {subject}.",
            f"Show the {table_label} that meet this filter.",
            f"Which {table_label} match the requested condition?",
            f"Please retrieve the filtered {table_label}.",
            f"Return only the matching {table_label}.",
            f"I need the {table_label} satisfying the condition.",
        ]
    if category == "ORDER_BY":
        return [
            f"Sort {subject}.",
            f"List {subject} in the requested order.",
            f"Show ordered {table_label}.",
            f"Please display {table_label} sorted as specified.",
            f"Return the ordered {table_label} list.",
        ]
    if category == "LIMIT":
        return [
            f"Show a small page of {table_label}.",
            f"Return the requested slice of {table_label}.",
            f"Give me a limited set of {table_label}.",
            f"Please display this page of {table_label}.",
            f"Fetch the limited {table_label} results.",
        ]
    if category == "DISTINCT":
        return [
            f"List the unique {subject}.",
            f"Show distinct {subject}.",
            f"Which different {subject} exist?",
            f"Return every unique {subject}.",
            f"Please display deduplicated {subject}.",
        ]
    if category == "COUNT":
        return [
            f"Count the {table_label}.",
            f"How many {table_label} match this request?",
            f"Return the number of {table_label}.",
            f"Please calculate the {table_label} count.",
            f"Give me the total {table_label}.",
        ]
    if category in {"AVG", "MIN", "MAX", "SUM"}:
        aggregate_name = {"AVG": "average", "MIN": "lowest", "MAX": "highest", "SUM": "total"}[category]
        return [
            f"Calculate the {aggregate_name} {subject}.",
            f"What is the {aggregate_name} value for {subject}?",
            f"Show the {aggregate_name} {subject}.",
            f"Please return the {aggregate_name} for {subject}.",
            f"Give me the {aggregate_name} measurement for {subject}.",
        ]
    if category == "GROUP_BY":
        return [
            f"Break down {table_label} by {subject}.",
            f"Group {table_label} using {subject}.",
            f"Show counts of {table_label} for each {subject}.",
            f"Please summarize {table_label} by {subject}.",
            f"Return the grouped {table_label} totals.",
        ]
    if category == "HAVING":
        return [
            f"Find grouped {table_label} where the group count is high enough.",
            f"Show {table_label} groups that pass the aggregate filter.",
            f"Which {table_label} groups satisfy the HAVING condition?",
            f"Please return qualifying grouped {table_label}.",
            f"List grouped {table_label} after applying the aggregate threshold.",
        ]
    if category == "JOIN":
        joined = " and ".join(_label(table) for table in functional_query["tables"])
        return [
            f"Show related records from {joined}.",
            f"List {joined} together.",
            f"Display matching rows across {joined}.",
            f"Please return the joined {joined} data.",
            f"Fetch records that connect {joined}.",
        ]
    if category in {"NESTED", "IN"}:
        return [
            f"Find {table_label} using the nested condition.",
            f"Show {table_label} selected by the subquery.",
            f"Which {table_label} appear in the nested result?",
            f"Please return {table_label} from the inner-query match.",
            f"List {table_label} whose keys are returned by the subquery.",
        ]
    if category == "EXISTS":
        return [
            f"Find {table_label} that have matching related rows.",
            f"Show {table_label} where related records exist.",
            f"Which {table_label} have associated data?",
            f"Please return {table_label} with existing relationships.",
            f"List {table_label} confirmed by the EXISTS condition.",
        ]
    return [
        _clean_sentence(functional_query["natural_language_query"]),
        f"Please {_lower_first(functional_query['natural_language_query'])}",
        f"Can you {_lower_first(functional_query['natural_language_query'])}",
        f"Return results for: {_lower_first(functional_query['natural_language_query'])}",
        f"I need to {_lower_first(functional_query['natural_language_query'])}",
    ]


def _deterministic_paraphrase_expansions(functional_query: dict[str, Any]) -> list[str]:
    canonical = _clean_sentence(functional_query["natural_language_query"])
    request = _lower_first(canonical)
    subject = _semantic_subject(functional_query)
    table_label = _label(functional_query["tables"][0]) if functional_query["tables"] else "records"
    category_label = _label(functional_query["category"])
    return [
        f"Can you {request}",
        f"Please {request}",
        f"I need to {request}",
        f"Could you {request}",
        f"Return the {table_label} results for this request: {request}",
        f"Fetch the {table_label} rows for this request: {request}",
        f"Give me the {category_label} result for {subject}.",
        f"I would like the {category_label} answer for {subject}.",
        f"Produce the matching {table_label} output for this request: {request}",
        f"Retrieve the database result for this request: {request}",
    ]


def _ollama_paraphrase_candidates(functional_query: dict[str, Any]) -> list[str]:
    model = os.getenv("SEMANTICSQL_BENCHMARK_PARAPHRASE_MODEL", "llama3.1:8b")
    if not _ollama_available():
        return []
    prompt = (
        "Generate 8 natural English paraphrases for this text-to-SQL request.\n"
        "Preserve the exact SQL meaning. Do not add filters, limits, or columns.\n"
        "Return one paraphrase per line. Do not number the lines.\n\n"
        f"Request: {functional_query['natural_language_query']}\n"
        f"SQL: {functional_query['expected_sql']}\n"
    )
    try:
        response = requests.post(
            OLLAMA_GENERATE_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "top_p": 1,
                    "seed": 0,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    payload = response.json()
    return [
        line.strip(" -\t")
        for line in str(payload.get("response", "")).splitlines()
        if line.strip(" -\t")
    ]


def _ollama_available() -> bool:
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=3)
        response.raise_for_status()
    except requests.RequestException:
        return False
    return True


def _valid_paraphrase_set(functional_query: dict[str, Any], paraphrases: list[str]) -> bool:
    accepted: list[str] = []
    for paraphrase in paraphrases:
        if not _is_valid_paraphrase(functional_query, paraphrase, accepted):
            return False
        accepted.append(paraphrase)
    return len(accepted) >= SEMANTIC_VARIANTS_PER_FUNCTIONAL


def _is_valid_paraphrase(functional_query: dict[str, Any], paraphrase: str, accepted: list[str]) -> bool:
    if not paraphrase or paraphrase in accepted:
        return False
    lowered = paraphrase.lower()
    if any(lowered.startswith(prefix) for prefix in ("show me show", "retrieve show", "give me show", "can you list show")):
        return False
    if "scenario " in lowered or "benchmark_subquery" in lowered:
        return False
    if len(paraphrase.split()) < 3:
        return False
    schema_terms = {_label(table).split()[0] for table in functional_query["tables"]}
    schema_terms.update(_label(column).split()[0] for column in functional_query["columns"])
    return _is_natural_english(paraphrase) and bool(schema_terms.intersection(set(lowered.replace("?", "").replace(".", "").split())))


def _is_natural_english(value: str) -> bool:
    words = value.replace("?", "").replace(".", "").split()
    if len(words) < 3:
        return False
    lowered = value.lower()
    repeated_prefixes = ("show me show", "retrieve show", "give me show", "can you list show")
    if any(lowered.startswith(prefix) for prefix in repeated_prefixes):
        return False
    if "scenario " in lowered or "benchmark_subquery" in lowered:
        return False
    if "  " in value:
        return False
    return value.endswith((".", "?"))


def _generate_invalid_queries(schema: SchemaInfo) -> list[dict[str, Any]]:
    invalid_queries: list[dict[str, Any]] = []
    invalid_nl_seen: set[str] = set()
    invalid_sql_seen: set[str] = set()
    index = 0
    while len(invalid_queries) < INVALID_COUNT:
        table = _table_at(schema, index)
        reason_type = index % 4
        if reason_type == 0:
            sql = f"SELECT * FROM missing_{table.name}_{index};"
            reason = "unknown_table"
            nlq = f"Show records from the missing {table.name} archive {index}"
        elif reason_type == 1:
            sql = f"SELECT missing_column_{index} FROM {table.name};"
            reason = "unknown_column"
            nlq = f"Show the missing column {index} for {table.name}"
        elif reason_type == 2:
            sql = f"SELECT * FROM {table.name} WHERE ;"
            reason = "invalid_syntax"
            nlq = f"Run malformed select request {index} for {table.name}"
        else:
            other_table = _table_at(schema, index + 1)
            sql = (
                f"SELECT * FROM {table.name} JOIN {other_table.name} "
                f"ON {table.name}.missing_id_{index} = {other_table.name}.missing_id_{index};"
            )
            reason = "invalid_join_condition"
            nlq = f"Join {table.name} with {other_table.name} using unavailable key pair {index}"

        candidate = {
            "id": f"I{len(invalid_queries) + 1:04d}",
            "benchmark_version": BENCHMARK_VERSION,
            "dataset": "invalid",
            "invalid_reason": reason,
            "natural_language_query": nlq,
            "expected_sql": sql,
        }
        if (
            candidate["natural_language_query"] not in invalid_nl_seen
            and candidate["expected_sql"] not in invalid_sql_seen
            and _invalid_candidate_fails_validation(schema, candidate)
        ):
            invalid_queries.append(candidate)
            invalid_nl_seen.add(candidate["natural_language_query"])
            invalid_sql_seen.add(candidate["expected_sql"])
        index += 1

    if len(invalid_queries) != INVALID_COUNT:
        raise ValueError(f"Expected {INVALID_COUNT} invalid queries, generated {len(invalid_queries)}.")

    return invalid_queries


def _invalid_candidate_fails_validation(schema: SchemaInfo, candidate: dict[str, Any]) -> bool:
    validation = validate_sql_against_schema(candidate["expected_sql"], schema)
    return not validation.valid and _matches_invalid_reason(candidate["invalid_reason"], validation.errors)


def _validate_benchmark(
    schema: SchemaInfo,
    functional_queries: list[dict[str, Any]],
    semantic_queries: list[dict[str, Any]],
    invalid_queries: list[dict[str, Any]],
    category_requirements: dict[str, int],
    difficulty_targets: dict[str, int],
) -> dict[str, Any]:
    errors: list[str] = []
    functional_by_id = {query["id"]: query for query in functional_queries}

    _validate_unique("functional natural language", [query["natural_language_query"] for query in functional_queries], errors)
    _validate_unique("semantic natural language", [query["natural_language_query"] for query in semantic_queries], errors)
    _validate_unique("invalid natural language", [query["natural_language_query"] for query in invalid_queries], errors)

    for dataset_name, queries in (("functional", functional_queries), ("semantic", semantic_queries)):
        for query in queries:
            validation = validate_sql_against_schema(query["expected_sql"], schema)
            if not validation.valid:
                errors.append(f"{dataset_name} query {query['id']} failed validation: {validation.errors}")

    for query in semantic_queries:
        functional_query_id = query.get("functional_query_id")
        if functional_query_id not in functional_by_id:
            errors.append(f"Semantic query {query['id']} references missing functional query.")
            continue
        if query["expected_sql"] != functional_by_id[functional_query_id]["expected_sql"]:
            errors.append(f"Semantic query {query['id']} does not preserve canonical SQL semantics.")

    invalid_reason_errors = 0
    for query in invalid_queries:
        validation = validate_sql_against_schema(query["expected_sql"], schema)
        if validation.valid:
            errors.append(f"Invalid query {query['id']} unexpectedly passed validation.")
            continue
        if not _matches_invalid_reason(query["invalid_reason"], validation.errors):
            invalid_reason_errors += 1
            errors.append(f"Invalid query {query['id']} failed for unexpected reason: {validation.errors}")
        query["expected_validation_errors"] = list(validation.errors)

    category_counts = Counter(query["category"] for query in functional_queries)
    for category, required_count in category_requirements.items():
        if category_counts[category] != required_count:
            errors.append(f"Category {category} expected {required_count}, got {category_counts[category]}.")

    difficulty_counts = Counter(query["difficulty"] for query in functional_queries)
    for difficulty, required_count in difficulty_targets.items():
        if difficulty_counts[difficulty] != required_count:
            errors.append(f"Difficulty {difficulty} expected {required_count}, got {difficulty_counts[difficulty]}.")

    mismatch_count = 0
    for query in functional_queries:
        computed = _difficulty_from_score(query["complexity_score"])
        if computed != query["difficulty"]:
            mismatch_count += 1
            errors.append(f"Difficulty mismatch for {query['id']}: labelled {query['difficulty']} but scored {computed}.")
        if not _category_matches_sql(query["category"], query["expected_sql"]):
            errors.append(f"Category mismatch for {query['id']}: {query['category']} does not match expected SQL.")

    duplicate_sql_count = len(functional_queries) - len({query["expected_sql"] for query in functional_queries})
    if duplicate_sql_count > max(3, math.ceil(len(functional_queries) * 0.02)):
        errors.append(f"Duplicate SQL templates exceed threshold: {duplicate_sql_count}.")

    if errors:
        raise ValueError("Benchmark consistency validation failed:\n" + "\n".join(errors[:25]))

    return {
        "valid": True,
        "errors": [],
        "duplicate_functional_sql": duplicate_sql_count,
        "invalid_reason_mismatches": invalid_reason_errors,
        "category_counts": dict(sorted(category_counts.items())),
        "difficulty_counts": dict(sorted(difficulty_counts.items())),
    }


def _analyze_schema_coverage(schema: SchemaInfo, functional_queries: list[dict[str, Any]]) -> dict[str, Any]:
    table_counts: Counter[str] = Counter()
    column_counts: Counter[str] = Counter()
    fk_counts: Counter[str] = Counter()
    chain_counts: Counter[str] = Counter()
    numeric_counts: Counter[str] = Counter()
    text_counts: Counter[str] = Counter()

    numeric_columns = {_qualified(table, column) for table in schema.tables for column in table.columns if _is_numeric(column)}
    text_columns = {_qualified(table, column) for table in schema.tables for column in table.columns if _is_text(column)}

    for query in functional_queries:
        for table_name in query["tables"]:
            table_counts[table_name] += 1
        for table_name, column_name in _query_column_pairs(schema, query).items():
            for column in column_name:
                qualified = f"{table_name}.{column}"
                column_counts[qualified] += 1
                if qualified in numeric_columns:
                    numeric_counts[qualified] += 1
                if qualified in text_columns:
                    text_counts[qualified] += 1
        for foreign_key in query.get("foreign_keys", []):
            fk_counts[foreign_key] += 1
        for relationship_chain in query.get("relationship_chain", []):
            chain_counts[relationship_chain] += 1

    tables = {
        table.name: {
            "covered": table_counts[table.name] > 0,
            "functional_queries": table_counts[table.name],
        }
        for table in schema.tables
    }
    columns = {
        f"{table.name}.{column.name}": {
            "covered": column_counts[f"{table.name}.{column.name}"] > 0,
            "functional_queries": column_counts[f"{table.name}.{column.name}"],
            "primary_key": column.primary_key,
            "numeric": f"{table.name}.{column.name}" in numeric_columns,
            "text": f"{table.name}.{column.name}" in text_columns,
        }
        for table in schema.tables
        for column in table.columns
    }
    foreign_keys = {
        _fk_key(foreign_key): {
            "covered": fk_counts[_fk_key(foreign_key)] > 0,
            "join_queries": fk_counts[_fk_key(foreign_key)],
        }
        for foreign_key in schema.foreign_keys
    }
    relationship_chains = {
        key: {
            "covered": count > 0,
            "join_queries": count,
        }
        for key, count in sorted(chain_counts.items())
    }

    components = [
        *(entry["covered"] for entry in tables.values()),
        *(entry["covered"] for entry in columns.values()),
        *(entry["covered"] for entry in foreign_keys.values()),
    ]
    if relationship_chains:
        components.extend(entry["covered"] for entry in relationship_chains.values())
    overall = round((sum(1 for covered in components if covered) / len(components)) * 100, 2) if components else 100.0

    return {
        "benchmark_version": BENCHMARK_VERSION,
        "tables": tables,
        "columns": columns,
        "foreign_keys": foreign_keys,
        "relationship_chains": relationship_chains,
        "aggregate_compatible_numeric_columns": {
            column: {"covered": numeric_counts[column] > 0, "aggregate_queries": numeric_counts[column]}
            for column in sorted(numeric_columns)
        },
        "searchable_text_columns": {
            column: {"covered": text_counts[column] > 0, "search_queries": text_counts[column]}
            for column in sorted(text_columns)
        },
        "overall_schema_coverage": overall,
    }


def _build_quality_report(
    coverage: dict[str, Any],
    statistics: dict[str, Any],
    consistency: dict[str, Any],
    category_requirements: dict[str, int],
) -> dict[str, Any]:
    total_queries = statistics["functional_queries"] + statistics["semantic_queries"]
    unique_sql = statistics["unique_sql_templates"]
    duplicate_penalty = round(max(0, 100 - (unique_sql / statistics["functional_queries"]) * 100), 2)
    diversity_score = round(min(100.0, (len(statistics["query_type_distribution"]) - 1) / len(category_requirements) * 100), 2)
    semantic_diversity_score = 100.0 if statistics["unique_natural_language_requests"] == statistics["total_queries"] else 95.0
    sql_complexity_score = _difficulty_balance_score(statistics["difficulty_distribution"])
    validation_score = 100.0 if consistency["valid"] else 0.0
    schema_coverage_score = coverage["overall_schema_coverage"]
    reproducibility_score = 100.0
    overall = round(
        (
            schema_coverage_score * 0.25
            + diversity_score * 0.15
            + semantic_diversity_score * 0.15
            + sql_complexity_score * 0.15
            + validation_score * 0.2
            + reproducibility_score * 0.1
        )
        - duplicate_penalty * 0.1,
        2,
    )
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "overall_score": overall,
        "schema_coverage_score": schema_coverage_score,
        "query_diversity_score": diversity_score,
        "semantic_diversity_score": semantic_diversity_score,
        "sql_complexity_score": sql_complexity_score,
        "duplicate_penalty": duplicate_penalty,
        "validation_score": validation_score,
        "reproducibility_score": reproducibility_score,
        "publication_readiness": "PASS" if overall >= 90 and schema_coverage_score >= 95 and validation_score == 100 else "REVIEW",
    }


def _build_paraphrase_audit(
    functional_queries: list[dict[str, Any]],
    semantic_queries: list[dict[str, Any]],
    coverage: dict[str, Any],
    quality: dict[str, Any],
) -> dict[str, Any]:
    functional_by_id = {query["id"]: query for query in functional_queries}
    semantic_validation_errors: list[str] = []
    grammar_errors: list[str] = []

    for query in semantic_queries:
        functional_query = functional_by_id.get(query["functional_query_id"])
        if functional_query is None:
            semantic_validation_errors.append(f"{query['id']} references missing functional query.")
            continue
        if query["expected_sql"] != functional_query["expected_sql"]:
            semantic_validation_errors.append(f"{query['id']} changed expected SQL semantics.")
        if not _is_natural_english(query["natural_language_query"]):
            grammar_errors.append(query["id"])

    return {
        "benchmark_version": BENCHMARK_VERSION,
        "duplicate_functional_queries": _duplicates([query["natural_language_query"] for query in functional_queries]),
        "duplicate_semantic_queries": _duplicates([query["natural_language_query"] for query in semantic_queries]),
        "duplicate_sql": _duplicates([query["expected_sql"] for query in functional_queries]),
        "grammar_validation": {
            "valid": not grammar_errors,
            "errors": grammar_errors,
        },
        "semantic_validation": {
            "valid": not semantic_validation_errors,
            "errors": semantic_validation_errors,
        },
        "coverage_statistics": {
            "overall_schema_coverage": coverage["overall_schema_coverage"],
            "covered_tables": sum(1 for table in coverage["tables"].values() if table["covered"]),
            "covered_columns": sum(1 for column in coverage["columns"].values() if column["covered"]),
            "covered_foreign_keys": sum(1 for key in coverage["foreign_keys"].values() if key["covered"]),
        },
        "overall_benchmark_quality": quality["overall_score"],
        "publication_readiness": quality["publication_readiness"],
    }


def _write_benchmark_files(
    output_dir: Path,
    schema: SchemaInfo,
    functional_queries: list[dict[str, Any]],
    semantic_queries: list[dict[str, Any]],
    invalid_queries: list[dict[str, Any]],
    coverage: dict[str, Any],
    statistics: dict[str, Any],
    quality: dict[str, Any],
    consistency: dict[str, Any],
    paraphrase_audit: dict[str, Any],
    category_requirements: dict[str, int],
    difficulty_targets: dict[str, int],
) -> None:
    datasets_dir = output_dir / "datasets"
    datasets_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat()
    datasets = {
        "functional": functional_queries,
        "semantic": semantic_queries,
        "invalid": invalid_queries,
    }

    for dataset_name, queries in datasets.items():
        _write_json(
            datasets_dir / f"{dataset_name}.json",
            {
                "benchmark_name": BENCHMARK_NAME,
                "benchmark_version": BENCHMARK_VERSION,
                "dataset": dataset_name,
                "queries": queries,
            },
        )

    all_queries = functional_queries + semantic_queries + invalid_queries
    manifest = {
        "benchmark_name": BENCHMARK_NAME,
        "benchmark_version": BENCHMARK_VERSION,
        "generation_timestamp": timestamp,
        "database_name": schema.database_name,
        "database_path": schema.database_path,
        "database_engine": schema.engine,
        "schema": {
            "tables": schema.table_count,
            "columns": schema.column_count,
            "primary_keys": schema.primary_key_count,
            "foreign_keys": schema.foreign_key_count,
        },
        "datasets": {
            "functional": len(functional_queries),
            "semantic": len(semantic_queries),
            "invalid": len(invalid_queries),
            "total": len(all_queries),
        },
        "query_categories": statistics["query_type_distribution"],
        "category_requirements": category_requirements,
        "difficulty_targets": difficulty_targets,
        "dataset_files": {
            "functional": "benchmark/datasets/functional.json",
            "semantic": "benchmark/datasets/semantic.json",
            "invalid": "benchmark/datasets/invalid.json",
        },
        "statistics_file": "benchmark/statistics.json",
        "schema_coverage_file": "benchmark/schema_coverage.json",
        "quality_file": "benchmark/benchmark_quality.json",
        "generator": "benchmark/generator.py",
        "database_adapter": "benchmark/adapters/sqlite.py",
        "consistency": consistency,
        "reproducibility": {
            "deterministic": True,
            "ordering": "schema objects, categories, templates, and variants are sorted or cycled deterministically",
            "random_seed": None,
        },
        "future_compatibility": [
            "rule_engines",
            "semantic_rule_repositories",
            "llm_sql_generators",
            "fine_tuned_models",
            "hybrid_retrieval_architectures",
            "postgresql",
            "mysql",
            "mariadb",
            "sql_server",
        ],
    }

    _write_json(output_dir / "manifest.json", manifest)
    _write_json(output_dir / "statistics.json", statistics)
    _write_json(output_dir / "schema_coverage.json", coverage)
    _write_json(output_dir / "benchmark_quality.json", quality)
    _write_json(output_dir / "paraphrase_audit.json", paraphrase_audit)


def _build_statistics(
    functional_queries: list[dict[str, Any]],
    semantic_queries: list[dict[str, Any]],
    invalid_queries: list[dict[str, Any]],
) -> dict[str, Any]:
    all_queries = functional_queries + semantic_queries + invalid_queries
    valid_queries = functional_queries + semantic_queries
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "total_queries": len(all_queries),
        "functional_queries": len(functional_queries),
        "semantic_queries": len(semantic_queries),
        "invalid_queries": len(invalid_queries),
        "average_query_length": round(mean(len(query["natural_language_query"]) for query in all_queries), 2),
        "average_sql_length": round(mean(len(query["expected_sql"]) for query in all_queries), 2),
        "query_type_distribution": dict(sorted(Counter(query.get("category", "INVALID") for query in all_queries).items())),
        "difficulty_distribution": dict(sorted(Counter(query.get("difficulty", "invalid") for query in all_queries).items())),
        "valid_workload_difficulty_percentages": {
            difficulty: round((count / len(valid_queries)) * 100, 2)
            for difficulty, count in sorted(Counter(query["difficulty"] for query in valid_queries).items())
        },
        "unique_sql_templates": len({query["expected_sql"] for query in functional_queries}),
        "duplicate_functional_sql": len(functional_queries) - len({query["expected_sql"] for query in functional_queries}),
        "unique_natural_language_requests": len({query["natural_language_query"] for query in all_queries}),
        "average_complexity_score": round(mean(query.get("complexity_score", 0) for query in valid_queries), 2),
    }


def _record(
    category: str,
    _generation_difficulty: str,
    natural_language_query: str,
    expected_sql: str,
    tables: list[str],
    columns: list[str],
    foreign_keys: list[str] | None = None,
    relationship_chain: list[str] | None = None,
) -> dict[str, Any]:
    complexity_score = _sql_complexity_score(expected_sql)
    difficulty = _difficulty_from_score(complexity_score)
    return {
        "category": category,
        "difficulty": difficulty,
        "natural_language_query": natural_language_query,
        "expected_sql": expected_sql,
        "tables": sorted(set(tables)),
        "columns": sorted(set(columns)),
        "foreign_keys": sorted(set(foreign_keys or [])),
        "relationship_chain": sorted(set(relationship_chain or [])),
        "complexity_score": complexity_score,
    }


def _sql_complexity_score(sql: str) -> int:
    expression = sqlglot.parse_one(sql, read="sqlite")
    score = 1
    score += len(list(expression.find_all(exp.Join))) * 2
    score += len(list(expression.find_all(exp.Subquery))) * 2
    score += len(list(expression.find_all(exp.Exists))) * 3
    score += len(list(expression.find_all(exp.In))) * 2
    score += len(list(expression.find_all(exp.Group))) * 2
    score += len(list(expression.find_all(exp.Having))) * 2
    score += len(list(expression.find_all(exp.Order))) * 1
    for aggregate in expression.find_all(exp.AggFunc):
        score += 1 if aggregate.key.upper() == "COUNT" else 2
    return score


def _difficulty_from_score(score: int) -> str:
    if score <= 2:
        return "easy"
    if score <= 5:
        return "medium"
    return "hard"


def _category_matches_sql(category: str, sql: str) -> bool:
    expression = sqlglot.parse_one(sql, read="sqlite")
    if category == "SELECT":
        return not any(
            list(expression.find_all(node_type))
            for node_type in (exp.Where, exp.Order, exp.Limit, exp.Distinct, exp.Join, exp.Group, exp.Having, exp.Subquery)
        )
    if category == "WHERE":
        return bool(list(expression.find_all(exp.Where)))
    if category == "ORDER_BY":
        return bool(list(expression.find_all(exp.Order)))
    if category == "LIMIT":
        return bool(list(expression.find_all(exp.Limit)))
    if category == "DISTINCT":
        return bool(list(expression.find_all(exp.Distinct)))
    if category == "COUNT":
        return "COUNT(" in sql.upper()
    if category in {"AVG", "MIN", "MAX", "SUM"}:
        return f"{category}(" in sql.upper()
    if category == "GROUP_BY":
        return bool(list(expression.find_all(exp.Group))) and not list(expression.find_all(exp.Having))
    if category == "HAVING":
        return bool(list(expression.find_all(exp.Having)))
    if category == "JOIN":
        return bool(list(expression.find_all(exp.Join)))
    if category == "NESTED":
        return bool(list(expression.find_all(exp.Subquery)))
    if category == "IN":
        return bool(list(expression.find_all(exp.In)))
    if category == "EXISTS":
        return bool(list(expression.find_all(exp.Exists)))
    return False


def _complexity_score_for_difficulty(difficulty: str) -> int:
    return {
        "easy": 2,
        "medium": 4,
        "hard": 7,
    }[difficulty]


def _difficulty_balance_score(distribution: dict[str, int]) -> float:
    total_valid = distribution.get("easy", 0) + distribution.get("medium", 0) + distribution.get("hard", 0)
    if not total_valid:
        return 0.0
    targets = {"easy": 35.0, "medium": 40.0, "hard": 25.0}
    deviation = sum(abs((distribution.get(label, 0) / total_valid) * 100 - target) for label, target in targets.items())
    return round(max(0.0, 100.0 - deviation), 2)


def _matches_invalid_reason(reason: str, errors: tuple[str, ...]) -> bool:
    joined = " ".join(errors).lower()
    return {
        "unknown_table": "unknown table",
        "unknown_column": "unknown column",
        "invalid_syntax": "syntax error",
        "invalid_join_condition": "unknown column",
    }[reason] in joined


def _validate_unique(label: str, values: list[str], errors: list[str]) -> None:
    duplicates = len(values) - len(set(values))
    if duplicates:
        errors.append(f"{label} contains {duplicates} duplicates.")


def _validate_no_duplicates(label: str, queries: list[dict[str, Any]]) -> None:
    nl_duplicates = _duplicates([query["natural_language_query"] for query in queries])
    sql_duplicates = _duplicates([query["expected_sql"] for query in queries]) if label == "functional queries" else []
    if nl_duplicates or sql_duplicates:
        details = []
        if nl_duplicates:
            details.append(f"duplicate natural language: {nl_duplicates[:5]}")
        if sql_duplicates:
            details.append(f"duplicate SQL: {sql_duplicates[:5]}")
        raise ValueError(f"{label} are not unique: {'; '.join(details)}")


def _duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def _load_paraphrase_cache() -> dict[str, list[str]]:
    if not PARAPHRASE_CACHE_PATH.exists():
        return {}
    try:
        payload = json.loads(PARAPHRASE_CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {
        str(key): [str(value) for value in values]
        for key, values in payload.items()
        if isinstance(values, list)
    }


def _save_paraphrase_cache(paraphrase_cache: dict[str, list[str]]) -> None:
    PARAPHRASE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PARAPHRASE_CACHE_PATH.write_text(
        json.dumps(paraphrase_cache, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _non_null_predicate(column: ColumnInfo) -> str:
    return f"{column.name} IS NOT NULL"


def _aggregate_filter(table: TableInfo, column: ColumnInfo, index: int) -> str:
    text_column = _text_column(table, index)
    if index % 3 == 0 and text_column is not None:
        return f" WHERE {text_column.name} IS NOT NULL AND LENGTH({text_column.name}) >= {index + 1}"
    if index % 3 == 1:
        return f" WHERE {column.name} >= {index}"
    return ""


def _nl_select(table: TableInfo, projection: list[str], index: int) -> str:
    subject = _columns_subject(table, projection)
    templates = (
        f"List {subject}.",
        f"Show {subject}.",
        f"Display {subject}.",
        f"Which {subject} are stored?",
        f"Return {subject}.",
    )
    return templates[index % len(templates)]


def _nl_where(table: TableInfo, column: ColumnInfo, index: int) -> str:
    label = _label(table.name)
    column_label = _label(column.name)
    if _is_numeric(column):
        comparator = COMPARISON_WORDS[index % len(COMPARISON_WORDS)]
        value = index
        return f"Show {label} with {column_label} {comparator} {value}."
    if _is_text(column):
        return f"Show {label} where {column_label} has at least {index + 1} characters."
    return f"Show {label} where {column_label} is available."


def _nl_order(table: TableInfo, column: ColumnInfo, direction: str, index: int) -> str:
    direction_text = "ascending" if direction == "ASC" else "descending"
    templates = (
        f"List the first {5 + index} {_label(table.name)} ordered by {_label(column.name)} {direction_text}.",
        f"Show {5 + index} {_label(table.name)} sorted by {_label(column.name)} in {direction_text} order.",
        f"Return {5 + index} {_label(table.name)} ranked by {_label(column.name)} {direction_text}.",
    )
    return templates[index % len(templates)]


def _nl_limit(table: TableInfo, limit: int, index: int) -> str:
    templates = (
        f"Show {limit} {_label(table.name)} records from this page.",
        f"Return a page of {limit} {_label(table.name)}.",
        f"List the next {limit} {_label(table.name)} records.",
    )
    return templates[index % len(templates)]


def _nl_distinct(table: TableInfo, column: ColumnInfo, index: int) -> str:
    templates = (
        f"List unique {_label(column.name)} values from {_label(table.name)} where {_filter_phrase(column, index)}.",
        f"Show distinct {_label(column.name)} in {_label(table.name)} after filtering for {_filter_phrase(column, index)}.",
        f"Which different {_label(column.name)} values exist for {_label(table.name)} with {_filter_phrase(column, index)}?",
    )
    return templates[index % len(templates)]


def _nl_count(table: TableInfo, column: ColumnInfo, index: int) -> str:
    templates = (
        f"Count {_label(table.name)} records where {_filter_phrase(column, index)}.",
        f"How many {_label(table.name)} have {_filter_phrase(column, index)}?",
        f"Return the number of {_label(table.name)} after filtering for {_filter_phrase(column, index)}.",
    )
    return templates[index % len(templates)]


def _nl_aggregate(category: str, table: TableInfo, column: ColumnInfo, index: int) -> str:
    aggregate_name = {
        "AVG": "average",
        "MIN": "lowest",
        "MAX": "highest",
        "SUM": "total",
    }[category]
    scope = _aggregate_scope_phrase(table, column, index)
    templates = (
        f"Calculate the {aggregate_name} {_label(column.name)} for {_label(table.name)} {scope}.",
        f"What is the {aggregate_name} {_label(column.name)} in {_label(table.name)} {scope}?",
        f"Show the {aggregate_name} {_label(column.name)} value for {_label(table.name)} {scope}.",
    )
    return templates[index % len(templates)]


def _nl_group_by(table: TableInfo, column: ColumnInfo, index: int) -> str:
    templates = (
        f"Break down {_label(table.name)} by {_label(column.name)} where {_filter_phrase(column, index)}.",
        f"Count {_label(table.name)} for each {_label(column.name)} after filtering for {_filter_phrase(column, index)}.",
        f"Summarize {_label(table.name)} grouped by {_label(column.name)} with {_filter_phrase(column, index)}.",
    )
    return templates[index % len(templates)]


def _nl_having(table: TableInfo, column: ColumnInfo, index: int) -> str:
    minimum_count = index
    templates = (
        f"Show {_label(table.name)} groups by {_label(column.name)} with more than {minimum_count} records.",
        f"List {_label(column.name)} groups in {_label(table.name)} whose counts exceed {minimum_count}.",
        f"Find {_label(table.name)} grouped by {_label(column.name)} after applying count threshold {minimum_count}.",
    )
    return templates[index % len(templates)]


def _nl_nested(source: TableInfo, target: TableInfo, index: int) -> str:
    templates = (
        f"Find {_label(source.name)} connected through nested {_label(target.name)} results for lookup {index + 1}.",
        f"Show {_label(source.name)} selected by nested lookup {index + 1} on {_label(target.name)}.",
        f"Return {_label(source.name)} whose related {_label(target.name)} values appear in subquery pass {index + 1}.",
    )
    return templates[index % len(templates)]


def _nl_nested_self(table: TableInfo, column: ColumnInfo, index: int) -> str:
    templates = (
        f"Show {_label(table.name)} whose keys appear in a subquery where {_filter_phrase(column, index)}.",
        f"Find {_label(table.name)} selected by a nested condition with {_filter_phrase(column, index)}.",
        f"Return {_label(table.name)} using a subquery filtered for {_filter_phrase(column, index)}.",
    )
    return templates[index % len(templates)]


def _nl_in(table: TableInfo, primary_key: str, column: ColumnInfo, index: int) -> str:
    templates = (
        f"Show {_label(table.name)} whose {_label(primary_key)} is in a subquery where {_filter_phrase(column, index)}.",
        f"Find {_label(table.name)} selected by an IN query with {_filter_phrase(column, index)}.",
        f"Return {_label(table.name)} where {_label(primary_key)} appears in the grouped inner result for {_filter_phrase(column, index)}.",
    )
    return templates[index % len(templates)]


def _nl_exists(source: TableInfo, target: TableInfo, index: int) -> str:
    templates = (
        f"Show {_label(source.name)} that have matching {_label(target.name)} for existence check {index + 1}.",
        f"Find {_label(source.name)} where related {_label(target.name)} records exist in pass {index + 1}.",
        f"Return {_label(source.name)} with confirmed {_label(target.name)} relationships for check {index + 1}.",
    )
    return templates[index % len(templates)]


def _nl_join_chain(source: TableInfo, middle: TableInfo, target: TableInfo, index: int) -> str:
    templates = (
        f"Show up to {10 + index} {_label(source.name)}, {_label(middle.name)}, and {_label(target.name)} joined together.",
        f"List {10 + index} {_label(source.name)} connected through {_label(middle.name)} to {_label(target.name)}.",
        f"Return {10 + index} related {_label(source.name)} and {_label(target.name)} records through {_label(middle.name)}.",
    )
    return templates[index % len(templates)]


def _nl_join(source: TableInfo, target: TableInfo, index: int) -> str:
    templates = (
        f"Show up to {10 + index} {_label(source.name)} with their related {_label(target.name)}.",
        f"List {10 + index} matching {_label(source.name)} and {_label(target.name)} records.",
        f"Return {10 + index} joined {_label(source.name)} and {_label(target.name)} data.",
    )
    return templates[index % len(templates)]


def _semantic_subject(functional_query: dict[str, Any]) -> str:
    columns = functional_query.get("columns") or []
    tables = functional_query.get("tables") or []
    if columns and tables:
        return f"{', '.join(_label(column) for column in columns)} for {_label(tables[0])}"
    if tables:
        return _label(tables[0])
    return "records"


def _columns_subject(table: TableInfo, columns: list[str]) -> str:
    if len(columns) == len(table.columns):
        return _label(table.name)
    return f"{', '.join(_label(column) for column in columns)} from {_label(table.name)}"


def _filter_phrase(column: ColumnInfo, index: int) -> str:
    if _is_numeric(column):
        return f"{_label(column.name)} is at least {index}"
    if _is_text(column):
        return f"{_label(column.name)} has at least {index + 1} characters"
    return f"{_label(column.name)} is available"


def _aggregate_scope_phrase(table: TableInfo, column: ColumnInfo, index: int) -> str:
    text_column = _text_column(table, index)
    if index % 3 == 0 and text_column is not None:
        return f"where {_filter_phrase(text_column, index)}"
    if index % 3 == 1:
        return f"where {_filter_phrase(column, index)}"
    return "across all records"


def _label(value: str) -> str:
    return value.replace("_", " ").strip().lower()


def _lower_first(value: str) -> str:
    cleaned = _clean_sentence(value)
    return cleaned[:1].lower() + cleaned[1:] if cleaned else cleaned


def _clean_sentence(value: str) -> str:
    cleaned = " ".join(str(value).strip().split())
    cleaned = cleaned.strip("\"'`")
    cleaned = cleaned.rstrip(".")
    return f"{cleaned}." if cleaned and not cleaned.endswith("?") else cleaned


def _query_column_pairs(schema: SchemaInfo, query: dict[str, Any]) -> dict[str, list[str]]:
    table_map = {table.name: table for table in schema.tables}
    pairs: dict[str, list[str]] = defaultdict(list)
    for table_name in query["tables"]:
        table = table_map[table_name]
        if "*" in query["expected_sql"]:
            pairs[table_name].extend(table.column_names)
    for column_name in query["columns"]:
        for table_name in query["tables"]:
            if column_name in table_map[table_name].column_names:
                pairs[table_name].append(column_name)
    return {table_name: sorted(set(columns)) for table_name, columns in pairs.items()}


def _table_at(schema: SchemaInfo, index: int) -> TableInfo:
    return schema.tables[index % len(schema.tables)]


def _relation_at(schema: SchemaInfo, index: int) -> ForeignKeyInfo | None:
    if not schema.foreign_keys:
        return None
    return schema.foreign_keys[index % len(schema.foreign_keys)]


def _relation_tables(schema: SchemaInfo, relation: ForeignKeyInfo) -> tuple[TableInfo, TableInfo]:
    table_map = {table.name: table for table in schema.tables}
    return table_map[relation.source_table], table_map[relation.target_table]


def _relationship_chain(schema: SchemaInfo, relation: ForeignKeyInfo) -> list[ForeignKeyInfo]:
    for next_relation in schema.foreign_keys:
        if relation.target_table == next_relation.source_table and _fk_key(next_relation) != _fk_key(relation):
            return [relation, next_relation]
        if relation.source_table == next_relation.source_table and _fk_key(next_relation) != _fk_key(relation):
            return [relation, next_relation]
    return [relation]


def _projection(table: TableInfo, index: int) -> list[str]:
    columns = list(table.column_names)
    width = min(len(columns), 1 + index % min(3, len(columns)))
    start = index % len(columns)
    return [columns[(start + offset) % len(columns)] for offset in range(width)]


def _predicate(column: ColumnInfo, index: int) -> str:
    if _is_numeric(column):
        return f"{column.name} >= {index}"
    if _is_text(column):
        return f"{column.name} IS NOT NULL AND LENGTH({column.name}) >= {index + 1}"
    return f"{column.name} IS NOT NULL"


def _column_at(table: TableInfo, index: int) -> ColumnInfo:
    return table.columns[index % len(table.columns)]


def _text_column(table: TableInfo, index: int) -> ColumnInfo | None:
    columns = [column for column in table.columns if _is_text(column)]
    return columns[index % len(columns)] if columns else None


def _numeric_column(table: TableInfo, index: int) -> ColumnInfo | None:
    columns = [column for column in table.columns if _is_numeric(column) and not column.primary_key]
    return columns[index % len(columns)] if columns else None


def _first_table_with_numeric(schema: SchemaInfo) -> TableInfo:
    return next(table for table in schema.tables if any(_is_numeric(column) and not column.primary_key for column in table.columns))


def _table_containing(schema: SchemaInfo, column_name: str, preferred: TableInfo) -> TableInfo:
    if column_name in preferred.column_names:
        return preferred
    return next(table for table in schema.tables if column_name in table.column_names)


def _qualified(table: TableInfo, column: ColumnInfo) -> str:
    return f"{table.name}.{column.name}"


def _fk_key(foreign_key: ForeignKeyInfo) -> str:
    return f"{foreign_key.source_table}.{foreign_key.source_column} -> {foreign_key.target_table}.{foreign_key.target_column}"


def _is_text(column: ColumnInfo) -> bool:
    return any(token in column.type for token in ("CHAR", "CLOB", "TEXT", "VARCHAR"))


def _is_numeric(column: ColumnInfo) -> bool:
    return any(token in column.type for token in ("INT", "REAL", "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE"))


def _unique(values: list[str]) -> list[str]:
    return sorted(set(values))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
