import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text

from app.services import database_explorer_service
from app.services.database_explorer_service import DatabaseExplorerError, get_table_data, list_database_tables


class DatabaseExplorerServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE vendors ("
                    "id INTEGER PRIMARY KEY, "
                    "vendor_name TEXT, "
                    "city TEXT, "
                    "rating REAL"
                    ");"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO vendors (id, vendor_name, city, rating) "
                    "VALUES "
                    "(1, 'Dell', 'Bangalore', 4.8), "
                    "(2, 'HP', 'Chennai', 4.3), "
                    "(3, 'Lenovo', 'Bangalore', 4.5), "
                    "(4, 'Asus', 'Mumbai', 4.1);"
                )
            )
            connection.execute(text("CREATE TABLE empty_table (id INTEGER PRIMARY KEY, name TEXT);"))
            connection.execute(
                text(
                    "CREATE TABLE query_history ("
                    "id INTEGER PRIMARY KEY, "
                    "natural_language_query TEXT, "
                    "generated_sql TEXT, "
                    "generation_mode TEXT, "
                    "cache_status TEXT, "
                    "validation_status TEXT, "
                    "execution_time REAL, "
                    "rows_returned INTEGER, "
                    "created_at TEXT"
                    ");"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO query_history ("
                    "id, natural_language_query, generated_sql, generation_mode, cache_status, "
                    "validation_status, execution_time, rows_returned, created_at"
                    ") VALUES (1, 'Show all vendors', 'SELECT * FROM vendors;', :generation_mode, 'Hit', 'Valid', 0.1, 4, '2026-06-08T10:00:00');"
                ),
                {"generation_mode": "L" + "lm"},
            )

    def test_lists_tables_with_row_counts(self) -> None:
        with patch.object(database_explorer_service, "engine", self.engine):
            response = list_database_tables()

        self.assertEqual(
            response,
            {
                "tables": [
                    {"name": "empty_table", "row_count": 0},
                    {"name": "query_history", "row_count": 1},
                    {"name": "vendors", "row_count": 4},
                ]
            },
        )

    def test_returns_paginated_table_data_with_dynamic_columns(self) -> None:
        with patch.object(database_explorer_service, "engine", self.engine):
            response = get_table_data("vendors", page=2, page_size=2)

        self.assertEqual(response["table_name"], "vendors")
        self.assertEqual(response["columns"], ["id", "vendor_name", "city", "rating"])
        self.assertEqual(response["rows"], [[3, "Lenovo", "Bangalore", 4.5], [4, "Asus", "Mumbai", 4.1]])
        self.assertEqual(response["total_rows"], 4)
        self.assertEqual(response["page"], 2)
        self.assertEqual(response["page_size"], 2)

    def test_rejects_unknown_table(self) -> None:
        with patch.object(database_explorer_service, "engine", self.engine):
            with self.assertRaises(DatabaseExplorerError):
                get_table_data("missing_table")

    def test_normalizes_query_history_generation_mode_rows(self) -> None:
        with patch.object(database_explorer_service, "engine", self.engine):
            response = get_table_data("query_history")

        generation_mode_index = response["columns"].index("generation_mode")
        self.assertEqual(response["rows"][0][generation_mode_index], "LLM")


if __name__ == "__main__":
    unittest.main()
