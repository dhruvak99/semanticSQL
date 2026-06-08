import logging
from dataclasses import dataclass

import sqlglot
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlglot import exp
from sqlglot.errors import ParseError

from app.db.session import engine

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SQLValidationResult:
    valid: bool
    errors: list[str]


def validate_sql(sql: str) -> SQLValidationResult:
    try:
        expression = sqlglot.parse_one(sql, read="sqlite")
    except ParseError as error:
        return SQLValidationResult(valid=False, errors=[f"SQL syntax error: {error}"])

    syntax_errors = _validate_select_shape(expression)
    if syntax_errors:
        return SQLValidationResult(valid=False, errors=syntax_errors)

    schema = _get_schema()
    table_errors, table_map = _validate_tables(expression, schema)
    column_errors = _validate_columns(expression, schema, table_map) if not table_errors else []
    errors = table_errors + column_errors

    return SQLValidationResult(valid=not errors, errors=errors)


def _validate_select_shape(expression: exp.Expression) -> list[str]:
    if not isinstance(expression, exp.Select):
        return ["Only SELECT statements can be validated for execution."]
    if not expression.expressions:
        return ["SQL syntax error: SELECT statement has no selected columns."]
    return []


def _get_schema() -> dict[str, set[str]]:
    try:
        database_inspector = inspect(engine)
        return {
            table_name: {
                column["name"]
                for column in database_inspector.get_columns(table_name)
            }
            for table_name in database_inspector.get_table_names()
        }
    except SQLAlchemyError:
        logger.exception("SQL validation schema inspection failed")
        return {}


def _validate_tables(
    expression: exp.Expression,
    schema: dict[str, set[str]],
) -> tuple[list[str], dict[str, str]]:
    errors: list[str] = []
    table_map: dict[str, str] = {}

    for table in expression.find_all(exp.Table):
        table_name = table.name
        if table_name not in schema:
            errors.append(f"Table '{table_name}' does not exist")
            continue

        table_map[table_name] = table_name
        table_map[table.alias_or_name] = table_name

    return errors, table_map


def _validate_columns(
    expression: exp.Expression,
    schema: dict[str, set[str]],
    table_map: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    referenced_tables = sorted(set(table_map.values()))

    for column in expression.find_all(exp.Column):
        column_name = column.name
        table_reference = column.table

        if table_reference:
            table_name = table_map.get(table_reference)
            if table_name and column_name not in schema.get(table_name, set()):
                errors.append(f"Column '{column_name}' does not exist in table '{table_name}'")
            continue

        matching_tables = [
            table_name
            for table_name in referenced_tables
            if column_name in schema.get(table_name, set())
        ]
        if not matching_tables:
            if len(referenced_tables) == 1:
                errors.append(f"Column '{column_name}' does not exist in table '{referenced_tables[0]}'")
            else:
                errors.append(f"Column '{column_name}' does not exist in referenced tables")

    return sorted(set(errors))
