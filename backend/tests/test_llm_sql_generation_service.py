import unittest
from unittest.mock import Mock, patch

from sqlalchemy import create_engine, text

from app.services import llm_sql_generation_service
from app.services.llm_sql_generation_service import (
    SCHEMA_MISMATCH,
    build_prompt,
    extract_schema_context,
    generate_sql,
)


class LLMSQLGenerationServiceTests(unittest.TestCase):
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
                    "CREATE TABLE products ("
                    "product_id INTEGER PRIMARY KEY, "
                    "product_name TEXT, "
                    "price REAL"
                    ");"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO products (product_id, product_name, price) "
                    "VALUES (1, 'Analytics Pack', 49.99), (2, 'Cache Booster', 19.99);"
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
            connection.execute(
                text(
                    "CREATE TABLE vendors ("
                    "vendor_id INTEGER PRIMARY KEY, "
                    "vendor_name TEXT, "
                    "rating REAL, "
                    "city TEXT"
                    ");"
                )
            )

    def test_extracts_runtime_schema_context(self) -> None:
        with patch.object(llm_sql_generation_service, "engine", self.engine):
            schema_context = extract_schema_context()

        self.assertIn("products(", schema_context)
        self.assertIn("product_id INTEGER", schema_context)
        self.assertIn("product_name TEXT", schema_context)
        self.assertIn("price REAL", schema_context)

    def test_builds_prompt_with_schema_and_request(self) -> None:
        prompt = build_prompt(
            "products(\nproduct_id INTEGER,\nproduct_name TEXT,\nprice REAL\n)",
            "Show all products",
        )

        self.assertIn("Generate only valid SQLite SQL or return SCHEMA_MISMATCH.", prompt)
        self.assertIn("Never invent tables.", prompt)
        self.assertIn("Semantic substitutions are forbidden.", prompt)
        self.assertIn("SCHEMA_MISMATCH", prompt)
        self.assertIn("products(", prompt)
        self.assertIn("Show all products", prompt)
        self.assertTrue(prompt.endswith("SQL:"))

    def test_generates_sql_for_runtime_table_using_ollama(self) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "SELECT * FROM products;"}
        mock_response.raise_for_status.return_value = None

        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post", return_value=mock_response) as post,
        ):
            result = generate_sql("Show all products")

        self.assertEqual(result.sql, "SELECT * FROM products;")
        self.assertEqual(result.generation_mode, "llm")
        request_payload = post.call_args.kwargs["json"]
        self.assertEqual(request_payload["model"], "llama3.1:8b")
        self.assertIn("products(", request_payload["prompt"])
        self.assertIn("Show all products", request_payload["prompt"])
        self.assertFalse(request_payload["stream"])

    def test_resolves_minor_table_spelling_mistakes_before_ollama(self) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "SELECT * FROM employees;"}
        mock_response.raise_for_status.return_value = None

        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post", return_value=mock_response) as post,
        ):
            result = generate_sql("Show all employeez")

        self.assertEqual(result.sql, "SELECT * FROM employees;")
        request_payload = post.call_args.kwargs["json"]
        self.assertIn("Show all employees", request_payload["prompt"])
        self.assertIn("employeez -> employees", request_payload["prompt"])

    def test_returns_schema_mismatch_for_semantic_substitutions(self) -> None:
        for query in ["Show all suppliers", "Show all customers", "Show all warehouses"]:
            with self.subTest(query=query):
                with (
                    patch.object(llm_sql_generation_service, "engine", self.engine),
                    patch("app.services.llm_sql_generation_service.requests.post") as post,
                ):
                    result = generate_sql(query)

                self.assertEqual(result.sql, SCHEMA_MISMATCH)
                post.assert_not_called()

    def test_returns_schema_mismatch_for_missing_requested_column(self) -> None:
        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post") as post,
        ):
            result = generate_sql("Show employee blood group")

        self.assertEqual(result.sql, SCHEMA_MISMATCH)
        post.assert_not_called()

    def test_allows_filter_values_for_existing_table(self) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "SELECT * FROM vendors WHERE city = 'Bangalore';"}
        mock_response.raise_for_status.return_value = None

        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post", return_value=mock_response) as post,
        ):
            result = generate_sql("Vendors in Bangalore")

        self.assertEqual(result.sql, "SELECT * FROM vendors WHERE city = 'Bangalore';")
        self.assertIn("Vendors in Bangalore", post.call_args.kwargs["json"]["prompt"])

    def test_allows_filter_values_with_explicit_column(self) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "SELECT * FROM vendors WHERE city = 'Bangalore';"}
        mock_response.raise_for_status.return_value = None

        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post", return_value=mock_response) as post,
        ):
            result = generate_sql("List vendors where city is Bangalore")

        self.assertEqual(result.sql, "SELECT * FROM vendors WHERE city = 'Bangalore';")
        self.assertIn("city", post.call_args.kwargs["json"]["prompt"])

    def test_allows_ordering_intent_for_existing_column(self) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "SELECT * FROM vendors ORDER BY rating DESC LIMIT 1;"
        }
        mock_response.raise_for_status.return_value = None

        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post", return_value=mock_response) as post,
        ):
            result = generate_sql("Highest rated vendor")

        self.assertEqual(result.sql, "SELECT * FROM vendors ORDER BY rating DESC LIMIT 1;")
        self.assertIn("rated -> rating", post.call_args.kwargs["json"]["prompt"])

    def test_allows_aggregation_intent_for_existing_column(self) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "SELECT AVG(rating) FROM vendors;"}
        mock_response.raise_for_status.return_value = None

        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post", return_value=mock_response) as post,
        ):
            result = generate_sql("Average vendor rating")

        self.assertEqual(result.sql, "SELECT AVG(rating) FROM vendors;")
        self.assertIn("Average vendors rating", post.call_args.kwargs["json"]["prompt"])

    def test_allows_rating_comparison_intent(self) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "SELECT * FROM vendors WHERE rating > 4;"}
        mock_response.raise_for_status.return_value = None

        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post", return_value=mock_response) as post,
        ):
            result = generate_sql("Show vendors with rating above 4")

        self.assertEqual(result.sql, "SELECT * FROM vendors WHERE rating > 4;")
        self.assertIn("Show vendors with rating above 4", post.call_args.kwargs["json"]["prompt"])

    def test_allows_salary_greater_than_comparison_intent(self) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "SELECT * FROM employees WHERE salary > 50000;"}
        mock_response.raise_for_status.return_value = None

        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post", return_value=mock_response) as post,
        ):
            result = generate_sql("Show employees with salary greater than 50000")

        self.assertEqual(result.sql, "SELECT * FROM employees WHERE salary > 50000;")
        self.assertIn(
            "Show employees with salary greater than 50000",
            post.call_args.kwargs["json"]["prompt"],
        )

    def test_allows_budget_less_than_comparison_intent(self) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "SELECT * FROM projects WHERE budget < 100000;"}
        mock_response.raise_for_status.return_value = None

        with (
            patch.object(llm_sql_generation_service, "engine", self.engine),
            patch("app.services.llm_sql_generation_service.requests.post", return_value=mock_response) as post,
        ):
            result = generate_sql("Projects with budget less than 100000")

        self.assertEqual(result.sql, "SELECT * FROM projects WHERE budget < 100000;")
        self.assertIn("Projects with budget less than 100000", post.call_args.kwargs["json"]["prompt"])


if __name__ == "__main__":
    unittest.main()
