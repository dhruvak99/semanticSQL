from typing import Any

from sqlalchemy import inspect

from app.db.session import engine


def get_database_schema() -> dict[str, Any]:
    database_inspector = inspect(engine)
    tables = []
    column_count = 0

    for table_name in sorted(database_inspector.get_table_names()):
        primary_keys = set(database_inspector.get_pk_constraint(table_name).get("constrained_columns", []))
        columns = [
            {
                "name": column["name"],
                "type": str(column["type"]).upper(),
                "primary_key": column["name"] in primary_keys or bool(column.get("primary_key")),
            }
            for column in database_inspector.get_columns(table_name)
        ]
        column_count += len(columns)
        tables.append(
            {
                "name": table_name,
                "column_count": len(columns),
                "columns": columns,
            }
        )

    return {
        "table_count": len(tables),
        "column_count": column_count,
        "tables": tables,
    }
