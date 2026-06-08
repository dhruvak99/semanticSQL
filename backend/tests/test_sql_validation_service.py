import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text

from app.services import sql_validation_service
from app.services.sql_validation_service import validate_sql


class SQLValidationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE employees ("
                    "employee_id INTEGER PRIMARY KEY, "
                    "name TEXT, "
                    "department TEXT, "
                    "salary REAL"
                    ");"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE projects ("
                    "project_id INTEGER PRIMARY KEY, "
                    "project_name TEXT, "
                    "budget REAL"
                    ");"
                )
            )

    def validate_with_test_schema(self, sql: str):
        with patch.object(sql_validation_service, "engine", self.engine):
            return validate_sql(sql)

    def test_valid_sql(self) -> None:
        result = self.validate_with_test_schema("SELECT * FROM employees;")

        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])

    def test_invalid_syntax(self) -> None:
        result = self.validate_with_test_schema("SELECT FROM employees;")

        self.assertFalse(result.valid)
        self.assertEqual(
            result.errors,
            ["SQL syntax error: SELECT statement has no selected columns."],
        )

    def test_invalid_table(self) -> None:
        result = self.validate_with_test_schema("SELECT * FROM employeez;")

        self.assertFalse(result.valid)
        self.assertEqual(result.errors, ["Table 'employeez' does not exist"])

    def test_invalid_column(self) -> None:
        result = self.validate_with_test_schema("SELECT budgets FROM projects;")

        self.assertFalse(result.valid)
        self.assertEqual(result.errors, ["Column 'budgets' does not exist in table 'projects'"])

    def test_valid_aggregate_sql(self) -> None:
        result = self.validate_with_test_schema("SELECT AVG(budget) FROM projects;")

        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])

    def test_invalid_aggregate_column(self) -> None:
        result = self.validate_with_test_schema("SELECT AVG(budgets) FROM projects;")

        self.assertFalse(result.valid)
        self.assertEqual(result.errors, ["Column 'budgets' does not exist in table 'projects'"])


if __name__ == "__main__":
    unittest.main()
