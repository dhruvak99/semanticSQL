from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from benchmark.adapters.base import ColumnInfo, ForeignKeyInfo, SchemaInfo, TableInfo


class SQLiteAdapter:
    engine_name = "SQLite"

    def __init__(self, database_url: str | None = None, database_path: str | Path | None = None) -> None:
        if database_url is None:
            resolved_path = Path(database_path) if database_path else _default_database_path()
            database_url = f"sqlite+pysqlite:///{resolved_path}"
        self.database_url = database_url
        self.engine: Engine = create_engine(database_url)

    def introspect(self) -> SchemaInfo:
        inspector = inspect(self.engine)
        table_names = sorted(inspector.get_table_names())
        tables: list[TableInfo] = []
        foreign_keys: list[ForeignKeyInfo] = []

        for table_name in table_names:
            primary_keys = set(inspector.get_pk_constraint(table_name).get("constrained_columns", []))
            columns = tuple(
                ColumnInfo(
                    name=column["name"],
                    type=str(column["type"]).upper(),
                    primary_key=column["name"] in primary_keys or bool(column.get("primary_key")),
                )
                for column in inspector.get_columns(table_name)
            )
            tables.append(TableInfo(name=table_name, columns=columns))

            for foreign_key in inspector.get_foreign_keys(table_name):
                referred_table = foreign_key.get("referred_table")
                constrained_columns = foreign_key.get("constrained_columns") or []
                referred_columns = foreign_key.get("referred_columns") or []
                for source_column, target_column in zip(constrained_columns, referred_columns, strict=False):
                    if referred_table:
                        foreign_keys.append(
                            ForeignKeyInfo(
                                source_table=table_name,
                                source_column=source_column,
                                target_table=referred_table,
                                target_column=target_column,
                            )
                        )

        inferred_foreign_keys = _infer_foreign_keys(tables, foreign_keys)
        return SchemaInfo(
            database_name=Path(str(self.engine.url.database or "semanticsql")).name,
            database_path=str(self.engine.url.database or self.database_url),
            engine=self.engine_name,
            tables=tuple(tables),
            foreign_keys=tuple(sorted(inferred_foreign_keys, key=lambda fk: (fk.source_table, fk.source_column))),
        )


def _default_database_path() -> Path:
    return Path(__file__).resolve().parents[2] / "backend" / "semanticsql.db"


def _infer_foreign_keys(
    tables: list[TableInfo],
    declared_foreign_keys: list[ForeignKeyInfo],
) -> set[ForeignKeyInfo]:
    foreign_keys = set(declared_foreign_keys)
    table_map = {table.name: table for table in tables}
    primary_key_lookup = {
        primary_key: table.name
        for table in tables
        for primary_key in table.primary_keys
    }

    for table in tables:
        for column in table.columns:
            if column.primary_key:
                continue
            target_table = primary_key_lookup.get(column.name)
            if target_table and target_table != table.name:
                foreign_keys.add(
                    ForeignKeyInfo(
                        source_table=table.name,
                        source_column=column.name,
                        target_table=target_table,
                        target_column=column.name,
                    )
                )
                continue

            if column.name.endswith("_id"):
                prefix = column.name.removesuffix("_id")
                candidate_names = {prefix, f"{prefix}s", f"{prefix}es"}
                for candidate_table in sorted(candidate_names):
                    if candidate_table in table_map and candidate_table != table.name:
                        target_primary_key = table_map[candidate_table].primary_keys
                        if target_primary_key:
                            foreign_keys.add(
                                ForeignKeyInfo(
                                    source_table=table.name,
                                    source_column=column.name,
                                    target_table=candidate_table,
                                    target_column=target_primary_key[0],
                                )
                            )
                        break

    return foreign_keys

