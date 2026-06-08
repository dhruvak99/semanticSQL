import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text

from app.services.llm_sql_generation_service import LLMSQLGenerationResult, SCHEMA_MISMATCH
from app.services.query_pipeline import process_semantic_query


class FakeCacheResult:
    hit = False
    similarity_score = 0.0
    entry = None


class FakeSemanticCache:
    def __init__(self) -> None:
        self.stored_payloads = []

    def generate_embedding(self, query: str) -> list[float]:
        return [1.0, 0.0] if "departments" in query.lower() else [0.0, 1.0]

    def search(self, embedding: list[float]) -> FakeCacheResult:
        return FakeCacheResult()

    def store(self, **kwargs) -> None:
        self.stored_payloads.append(kwargs)


class QueryPipelineTests(unittest.TestCase):
    @patch("app.services.query_pipeline.get_semantic_cache_service")
    @patch("app.services.query_pipeline.generate_sql_with_llm")
    @patch("app.services.query_pipeline.execute_query")
    def test_department_and_salary_queries_have_different_responses(
        self,
        execute_query_mock,
        generate_sql_with_llm_mock,
        get_cache_mock,
    ) -> None:
        get_cache_mock.return_value = FakeSemanticCache()
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

        self.assertEqual(department_response.generation_mode, "rule")
        self.assertEqual(salary_response.generation_mode, "rule")
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
        generate_sql_with_llm_mock.assert_not_called()

    @patch("app.services.query_pipeline.get_semantic_cache_service")
    @patch("app.services.query_pipeline.generate_sql_with_llm")
    @patch("app.services.database_service.engine")
    def test_rule_path_uses_generation_mode_rule(
        self,
        database_engine_mock,
        generate_sql_with_llm_mock,
        get_cache_mock,
    ) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        with engine.begin() as connection:
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
                    "INSERT INTO employees (employee_id, name, department, salary) "
                    "VALUES (1, 'Sarah Johnson', 'Finance', 88000.0);"
                )
            )

        database_engine_mock.connect.side_effect = engine.connect
        get_cache_mock.return_value = FakeSemanticCache()

        response = process_semantic_query("Show employees from Finance")

        self.assertEqual(response.generation_mode, "rule")
        self.assertEqual(response.generated_sql, "SELECT * FROM employees\nWHERE department = 'Finance';")
        self.assertEqual(response.rows_returned, 1)
        self.assertEqual(response.results[0]["department"], "Finance")
        generate_sql_with_llm_mock.assert_not_called()

    @patch("app.services.query_pipeline.get_semantic_cache_service")
    @patch("app.services.query_pipeline.generate_sql_with_llm")
    @patch("app.services.database_service.engine")
    def test_llm_path_uses_generation_mode_llm_and_executes_runtime_table(
        self,
        database_engine_mock,
        generate_sql_with_llm_mock,
        get_cache_mock,
    ) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE projects ("
                    "project_id INTEGER PRIMARY KEY, "
                    "project_name TEXT, "
                    "budget REAL"
                    ");"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO projects (project_id, project_name, budget) "
                    "VALUES (1, 'Semantic Cache Optimization', 125000.0), "
                    "(2, 'LLM SQL Generation', 185000.0);"
                )
            )

        fake_cache = FakeSemanticCache()
        database_engine_mock.connect.side_effect = engine.connect
        get_cache_mock.return_value = fake_cache
        generate_sql_with_llm_mock.return_value = LLMSQLGenerationResult(
            sql="SELECT AVG(budget) FROM projects;",
        )

        response = process_semantic_query("Average project budget")

        self.assertEqual(response.generation_mode, "llm")
        self.assertEqual(response.generated_sql, "SELECT AVG(budget) FROM projects;")
        self.assertEqual(response.rows_returned, 1)
        self.assertEqual(response.results, [{"AVG(budget)": 155000.0}])
        self.assertEqual(fake_cache.stored_payloads[0]["response_payload"]["generation_mode"], "llm")
        generate_sql_with_llm_mock.assert_called_once_with("Average project budget")

    @patch("app.services.query_pipeline.get_semantic_cache_service")
    @patch("app.services.query_pipeline.generate_sql_with_llm")
    @patch("app.services.query_pipeline.execute_query")
    @patch("app.services.sql_validation_service.engine")
    def test_validation_failure_skips_database_execution(
        self,
        validation_engine_mock,
        execute_query_mock,
        generate_sql_with_llm_mock,
        get_cache_mock,
    ) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE employees ("
                    "employee_id INTEGER PRIMARY KEY, "
                    "name TEXT"
                    ");"
                )
            )

        fake_cache = FakeSemanticCache()
        validation_engine_mock.connect.side_effect = engine.connect
        validation_engine_mock.dialect = engine.dialect
        get_cache_mock.return_value = fake_cache
        generate_sql_with_llm_mock.return_value = LLMSQLGenerationResult(
            sql="SELECT * FROM employeez;",
        )

        response = process_semantic_query("Show all employeez")

        self.assertEqual(response.generation_mode, "llm")
        self.assertEqual(response.validation_status, "invalid")
        self.assertEqual(response.validation_errors, ["Table 'employeez' does not exist"])
        self.assertEqual(response.rows_returned, 0)
        self.assertEqual(response.results, [])
        execute_query_mock.assert_not_called()
        self.assertEqual(fake_cache.stored_payloads[0]["response_payload"]["validation_errors"], response.validation_errors)

    @patch("app.services.query_pipeline.get_semantic_cache_service")
    @patch("app.services.query_pipeline.generate_sql_with_llm")
    @patch("app.services.query_pipeline.execute_query")
    def test_schema_mismatch_skips_database_execution_and_cache_store(
        self,
        execute_query_mock,
        generate_sql_with_llm_mock,
        get_cache_mock,
    ) -> None:
        fake_cache = FakeSemanticCache()
        get_cache_mock.return_value = fake_cache
        generate_sql_with_llm_mock.return_value = LLMSQLGenerationResult(sql=SCHEMA_MISMATCH)

        response = process_semantic_query("Show all suppliers")

        self.assertEqual(response.generation_mode, "llm")
        self.assertEqual(response.generated_sql, SCHEMA_MISMATCH)
        self.assertEqual(response.validation_status, "invalid")
        self.assertEqual(
            response.validation_errors,
            ["Requested table or column does not exist in the current schema."],
        )
        self.assertEqual(response.rows_returned, 0)
        self.assertEqual(response.results, [])
        execute_query_mock.assert_not_called()
        self.assertEqual(fake_cache.stored_payloads, [])


if __name__ == "__main__":
    unittest.main()
