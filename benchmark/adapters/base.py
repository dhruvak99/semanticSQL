from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    type: str
    primary_key: bool = False


@dataclass(frozen=True)
class ForeignKeyInfo:
    source_table: str
    source_column: str
    target_table: str
    target_column: str


@dataclass(frozen=True)
class TableInfo:
    name: str
    columns: tuple[ColumnInfo, ...]

    @property
    def primary_keys(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns if column.primary_key)

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)


@dataclass(frozen=True)
class SchemaInfo:
    database_name: str
    database_path: str
    engine: str
    tables: tuple[TableInfo, ...]
    foreign_keys: tuple[ForeignKeyInfo, ...]

    @property
    def table_count(self) -> int:
        return len(self.tables)

    @property
    def column_count(self) -> int:
        return sum(len(table.columns) for table in self.tables)

    @property
    def primary_key_count(self) -> int:
        return sum(len(table.primary_keys) for table in self.tables)

    @property
    def foreign_key_count(self) -> int:
        return len(self.foreign_keys)


class DatabaseAdapter(Protocol):
    engine_name: str

    def introspect(self) -> SchemaInfo:
        ...

