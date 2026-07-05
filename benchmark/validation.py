from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from benchmark.adapters.base import ForeignKeyInfo, SchemaInfo


@dataclass(frozen=True)
class BenchmarkValidationResult:
    valid: bool
    errors: tuple[str, ...]


def validate_sql_against_schema(sql: str, schema: SchemaInfo) -> BenchmarkValidationResult:
    try:
        expression = sqlglot.parse_one(sql, read="sqlite")
    except ParseError as error:
        return BenchmarkValidationResult(False, (f"SQL syntax error: {error}",))

    if not isinstance(expression, exp.Select):
        return BenchmarkValidationResult(False, ("Only SELECT statements are supported in benchmark SQL.",))

    schema_tables = {table.name: set(table.column_names) for table in schema.tables}
    table_aliases: dict[str, str] = {}
    table_errors: list[str] = []

    for table in expression.find_all(exp.Table):
        table_name = table.name
        if table_name not in schema_tables:
            table_errors.append(f"Unknown table '{table_name}'")
            continue
        table_aliases[table_name] = table_name
        table_aliases[table.alias_or_name] = table_name

    column_errors: list[str] = []
    if not table_errors:
        referenced_tables = sorted(set(table_aliases.values()))
        for column in expression.find_all(exp.Column):
            table_reference = column.table
            column_name = column.name
            if column_name == "*":
                continue
            if table_reference:
                table_name = table_aliases.get(table_reference)
                if table_name and column_name not in schema_tables.get(table_name, set()):
                    column_errors.append(f"Unknown column '{column_name}' in table '{table_name}'")
                continue

            matching_tables = [
                table_name
                for table_name in referenced_tables
                if column_name in schema_tables.get(table_name, set())
            ]
            if not matching_tables:
                if len(referenced_tables) == 1:
                    column_errors.append(f"Unknown column '{column_name}' in table '{referenced_tables[0]}'")
                else:
                    column_errors.append(f"Unknown column '{column_name}' in referenced tables")

    join_errors = _validate_joins(expression, schema) if not table_errors and not column_errors else []
    errors = tuple(sorted(set(table_errors + column_errors + join_errors)))
    return BenchmarkValidationResult(not errors, errors)


def _validate_joins(expression: exp.Expression, schema: SchemaInfo) -> list[str]:
    if not list(expression.find_all(exp.Join)):
        return []

    allowed_pairs = _foreign_key_pairs(schema.foreign_keys)
    errors: list[str] = []
    for equality in expression.find_all(exp.EQ):
        left = equality.left
        right = equality.right
        if not isinstance(left, exp.Column) or not isinstance(right, exp.Column):
            continue
        left_pair = (left.table, left.name)
        right_pair = (right.table, right.name)
        if (left_pair, right_pair) not in allowed_pairs and (right_pair, left_pair) not in allowed_pairs:
            errors.append(
                "Invalid JOIN condition "
                f"'{left.sql(dialect='sqlite')} = {right.sql(dialect='sqlite')}'"
            )

    return errors


def _foreign_key_pairs(foreign_keys: tuple[ForeignKeyInfo, ...]) -> set[tuple[tuple[str, str], tuple[str, str]]]:
    pairs: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    for foreign_key in foreign_keys:
        pairs.add(
            (
                (foreign_key.source_table, foreign_key.source_column),
                (foreign_key.target_table, foreign_key.target_column),
            )
        )
    return pairs
