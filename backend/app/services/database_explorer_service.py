from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import inspect, text

from app.db.session import engine
from app.services.query_history_service import normalize_generation_mode


class DatabaseExplorerError(ValueError):
    pass


def list_database_tables() -> dict[str, list[dict[str, Any]]]:
    database_inspector = inspect(engine)
    table_names = sorted(database_inspector.get_table_names())

    return {
        "tables": [
            {
                "name": table_name,
                "row_count": _get_table_row_count(table_name),
            }
            for table_name in table_names
        ]
    }


def get_table_data(table_name: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    normalized_page = max(page, 1)
    normalized_page_size = min(max(page_size, 1), 100)
    _validate_table_name(table_name)

    database_inspector = inspect(engine)
    columns = [column["name"] for column in database_inspector.get_columns(table_name)]
    total_rows = _get_table_row_count(table_name)
    offset = (normalized_page - 1) * normalized_page_size
    quoted_table_name = _quote_identifier(table_name)

    with engine.connect() as connection:
        result = connection.execute(
            text(f"SELECT * FROM {quoted_table_name} LIMIT :limit OFFSET :offset"),
            {"limit": normalized_page_size, "offset": offset},
        )
        rows = [
            [
                _serialize_table_value(table_name, columns[index], value)
                for index, value in enumerate(row)
            ]
            for row in result.fetchall()
        ]

    return {
        "table_name": table_name,
        "columns": columns,
        "rows": rows,
        "total_rows": total_rows,
        "page": normalized_page,
        "page_size": normalized_page_size,
    }


def _validate_table_name(table_name: str) -> None:
    database_inspector = inspect(engine)
    if table_name not in set(database_inspector.get_table_names()):
        raise DatabaseExplorerError(f"Table '{table_name}' does not exist")


def _get_table_row_count(table_name: str) -> int:
    _validate_table_name(table_name)
    quoted_table_name = _quote_identifier(table_name)
    with engine.connect() as connection:
        return int(connection.execute(text(f"SELECT COUNT(*) FROM {quoted_table_name}")).scalar_one())


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_table_value(table_name: str, column_name: str, value: Any) -> Any:
    if table_name == "query_history" and column_name == "generation_mode" and isinstance(value, str):
        return normalize_generation_mode(value)
    return _serialize_value(value)
