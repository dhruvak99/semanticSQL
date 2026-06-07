import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text

from app.services.database_service import (
    DatabaseErrorCode,
    DatabaseServiceError,
    _ensure_read_only_sql,
    execute_query,
)


class DatabaseServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE employees ("
                    "employee_id INTEGER PRIMARY KEY, "
                    "name TEXT NOT NULL, "
                    "department TEXT NOT NULL, "
                    "salary NUMERIC NOT NULL"
                    ")"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO employees "
                    "(employee_id, name, department, salary) VALUES "
                    "(1, 'Michael Brown', 'Finance', 95000), "
                    "(2, 'Sarah Johnson', 'Finance', 88000), "
                    "(3, 'David Wilson', 'Engineering', 75000)"
                )
            )

    def test_executes_read_only_queries_with_sqlalchemy(self) -> None:
        with patch("app.services.database_service.engine", self.engine):
            departments = execute_query(
                "SELECT DISTINCT department FROM employees ORDER BY department;"
            )
            counts = execute_query(
                "SELECT department, COUNT(*) AS employee_count "
                "FROM employees GROUP BY department ORDER BY department;"
            )
            empty_results = execute_query(
                "SELECT * FROM employees WHERE salary > 200000;"
            )

        self.assertEqual(
            departments,
            [{"department": "Engineering"}, {"department": "Finance"}],
        )
        self.assertEqual(
            counts,
            [
                {"department": "Engineering", "employee_count": 1},
                {"department": "Finance", "employee_count": 2},
            ],
        )
        self.assertEqual(empty_results, [])

    def test_allows_select_distinct_group_by_and_count(self) -> None:
        safe_sql_statements = [
            "SELECT DISTINCT department FROM employees;",
            "SELECT department, COUNT(*) AS employee_count FROM employees GROUP BY department;",
            "SELECT * FROM employees WHERE salary > 50000;",
        ]

        for sql in safe_sql_statements:
            with self.subTest(sql=sql):
                _ensure_read_only_sql(sql)

    def test_blocks_dangerous_sql(self) -> None:
        unsafe_sql_statements = [
            "DROP TABLE employees;",
            "TRUNCATE TABLE employees;",
            "DELETE FROM employees;",
            "UPDATE employees SET salary = 0;",
            "ALTER TABLE employees ADD COLUMN test INT;",
            "INSERT INTO employees (name) VALUES ('Bad');",
            "CREATE TABLE employees_archive (id INT);",
            "SELECT * FROM employees FOR UPDATE;",
            "SELECT * FROM employees INTO OUTFILE '/tmp/employees.csv';",
            "SELECT * FROM employees /* hidden operation */;",
        ]

        for sql in unsafe_sql_statements:
            with self.subTest(sql=sql):
                with self.assertRaises(DatabaseServiceError) as error:
                    _ensure_read_only_sql(sql)
                self.assertEqual(error.exception.code, DatabaseErrorCode.UNSAFE_SQL)

    def test_blocks_multiple_statements(self) -> None:
        with self.assertRaises(DatabaseServiceError) as error:
            _ensure_read_only_sql("SELECT * FROM employees; SELECT * FROM departments;")

        self.assertEqual(error.exception.code, DatabaseErrorCode.UNSAFE_SQL)


if __name__ == "__main__":
    unittest.main()
