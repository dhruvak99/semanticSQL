import unittest

from app.services.sql_generation_service import QueryType, generate_sql


class SQLGenerationServiceTests(unittest.TestCase):
    def test_lists_all_departments(self) -> None:
        result = generate_sql("List all departments")

        self.assertEqual(result.query_type, QueryType.LIST_DEPARTMENTS)
        self.assertEqual(result.sql, "SELECT DISTINCT department FROM employees;")

    def test_filters_employees_by_salary(self) -> None:
        result = generate_sql("Show employees with salary greater than 50000")

        self.assertEqual(result.query_type, QueryType.SALARY_FILTER)
        self.assertEqual(result.sql, "SELECT * FROM employees WHERE salary > 50000;")

    def test_counts_employees_by_department(self) -> None:
        result = generate_sql("Count employees in each department")

        self.assertEqual(result.query_type, QueryType.COUNT_BY_DEPARTMENT)
        self.assertEqual(
            result.sql,
            "SELECT department, COUNT(*) AS employee_count\n"
            "FROM employees\n"
            "GROUP BY department;",
        )

    def test_filters_employees_by_department(self) -> None:
        result = generate_sql("Show employees from department Finance")

        self.assertEqual(result.query_type, QueryType.DEPARTMENT_FILTER)
        self.assertEqual(
            result.sql,
            "SELECT * FROM employees\nWHERE department = 'Finance';",
        )

    def test_creates_employee_table(self) -> None:
        result = generate_sql("Create employee table with id, name, salary")

        self.assertEqual(result.query_type, QueryType.CREATE_EMPLOYEE_TABLE)
        self.assertEqual(
            result.sql,
            "CREATE TABLE employees (\n"
            "  id INT PRIMARY KEY AUTO_INCREMENT,\n"
            "  name VARCHAR(100) NOT NULL,\n"
            "  salary DECIMAL(12, 2) NOT NULL\n"
            ");",
        )


if __name__ == "__main__":
    unittest.main()
