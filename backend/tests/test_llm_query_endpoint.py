import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_sql_generation_service import LLMSQLGenerationResult


class LLMQueryEndpointTests(unittest.TestCase):
    def test_llm_generate_endpoint_returns_generated_sql(self) -> None:
        with patch(
            "app.api.v1.endpoints.query.generate_sql",
            return_value=LLMSQLGenerationResult(sql="SELECT * FROM products;"),
        ):
            client = TestClient(app)
            response = client.post(
                "/api/v1/query/llm-generate",
                json={"query": "Show all products"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "generated_sql": "SELECT * FROM products;",
                "generation_mode": "LLM",
            },
        )


if __name__ == "__main__":
    unittest.main()
