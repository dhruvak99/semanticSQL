import unittest
from unittest.mock import patch

from app.services.query_pipeline import process_semantic_query


class QueryPipelineTests(unittest.TestCase):
    @patch("app.services.query_pipeline.execute_query")
    def test_department_and_salary_queries_have_different_responses(self, execute_query_mock) -> None:
        execute_query_mock.side_effect = [
            [
                {"department": "Engineering"},
                {"department": "Finance"},
                {"department": "Human Resources"},
                {"department": "Operations"},
            ],
            [
                {"employee_id": 107, "name": "Michael Brown", "salary": 95000.0},
                {"employee_id": 104, "name": "Sarah Johnson", "salary": 88000.0},
            ],
        ]

        department_response = process_semantic_query("List all departments")
        salary_response = process_semantic_query("Show employees with salary greater than 50000")

        self.assertNotEqual(
            department_response.generated_sql,
            salary_response.generated_sql,
        )
        self.assertNotEqual(
            department_response.results,
            salary_response.results,
        )
        self.assertEqual(
            department_response.results,
            [
                {"department": "Engineering"},
                {"department": "Finance"},
                {"department": "Human Resources"},
                {"department": "Operations"},
            ],
        )
        self.assertTrue(
            all("employee_id" in row for row in salary_response.results)
        )
        execute_query_mock.assert_any_call("SELECT DISTINCT department FROM employees;")
        execute_query_mock.assert_any_call("SELECT * FROM employees WHERE salary > 50000;")


if __name__ == "__main__":
    unittest.main()
