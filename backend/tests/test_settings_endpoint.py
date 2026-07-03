import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.semantic_cache_service import get_semantic_cache_service


class SettingsEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.semantic_cache = get_semantic_cache_service()
        self.original_threshold = self.semantic_cache.get_threshold()

    def tearDown(self) -> None:
        self.semantic_cache.set_threshold(self.original_threshold)

    def test_returns_runtime_settings(self) -> None:
        payload = {
            "active_llm_model": "llama3.1:8b",
            "embedding_model": "all-MiniLM-L6-v2",
            "cache_backend": "Redis",
            "redis_url": "redis://localhost:6379/0",
            "similarity_threshold": 0.9,
            "ollama_url": "http://localhost:11434/api/generate",
            "database_engine": "SQLite",
            "database_url": "sqlite+pysqlite:///semanticsql.db",
            "python_version": "3.14.0",
            "semantic_sql_version": "0.1.0",
            "operating_system": "TestOS-1",
            "ollama_available": True,
            "redis_available": True,
        }

        with patch("app.api.v1.endpoints.settings.get_runtime_settings", return_value=payload):
            response = self.client.get("/api/v1/settings/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), payload)

    def test_settings_endpoint_returns_current_runtime_threshold(self) -> None:
        self.semantic_cache.set_threshold(0.85)

        with patch("app.services.settings_service._ollama_is_available", return_value=True):
            response = self.client.get("/api/v1/settings/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["similarity_threshold"], 0.85)

    def test_updates_runtime_cache_threshold(self) -> None:
        response = self.client.put(
            "/api/v1/settings/cache-threshold",
            json={"similarity_threshold": 0.85},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "similarity_threshold": 0.85,
                "message": "Semantic cache threshold updated successfully.",
            },
        )
        self.assertEqual(self.semantic_cache.get_threshold(), 0.85)

    def test_rejects_threshold_outside_valid_range(self) -> None:
        for invalid_threshold in (-0.01, 1.01):
            with self.subTest(threshold=invalid_threshold):
                response = self.client.put(
                    "/api/v1/settings/cache-threshold",
                    json={"similarity_threshold": invalid_threshold},
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(self.semantic_cache.get_threshold(), self.original_threshold)


if __name__ == "__main__":
    unittest.main()
