import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text

from app.services import schema_manager_service
from app.services.schema_manager_service import get_database_schema


class SchemaManagerServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE employees ("
                    "employee_id INTEGER PRIMARY KEY, "
                    "name TEXT, "
                    "department TEXT"
                    ");"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE vendors ("
                    "vendor_id INTEGER PRIMARY KEY, "
                    "vendor_name TEXT, "
                    "city TEXT, "
                    "rating REAL"
                    ");"
                )
            )

    def test_introspects_sqlite_tables_columns_and_primary_keys(self) -> None:
        with patch.object(schema_manager_service, "engine", self.engine):
            schema = get_database_schema()

        self.assertEqual(schema["table_count"], 2)
        self.assertEqual(schema["column_count"], 7)
        employees = next(table for table in schema["tables"] if table["name"] == "employees")
        self.assertEqual(employees["column_count"], 3)
        self.assertEqual(
            employees["columns"][0],
            {"name": "employee_id", "type": "INTEGER", "primary_key": True},
        )
        vendors = next(table for table in schema["tables"] if table["name"] == "vendors")
        self.assertEqual(vendors["columns"][-1], {"name": "rating", "type": "REAL", "primary_key": False})


if __name__ == "__main__":
    unittest.main()
