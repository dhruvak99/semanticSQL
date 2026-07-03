import unittest
from unittest.mock import Mock, patch

from app.services import settings_service
from app.services.model_runtime_state import get_active_model, set_active_model


class FakeSemanticCache:
    backend_name = "Redis"
    redis_available = True

    def get_threshold(self) -> float:
        return 0.85


class SettingsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_model = get_active_model()
        set_active_model("mistral:latest")

    def tearDown(self) -> None:
        set_active_model(self.original_model)

    def test_returns_live_runtime_configuration(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None

        with (
            patch.object(settings_service, "get_semantic_cache_service", return_value=FakeSemanticCache()),
            patch.object(settings_service.requests, "get", return_value=response) as ollama_get,
            patch.object(settings_service.platform, "python_version", return_value="3.14.0"),
            patch.object(settings_service.platform, "platform", return_value="TestOS-1"),
            patch.object(settings_service, "_get_semantic_sql_version", return_value="0.1.0"),
        ):
            result = settings_service.get_runtime_settings()

        self.assertEqual(result["active_llm_model"], "mistral:latest")
        self.assertEqual(result["embedding_model"], "all-MiniLM-L6-v2")
        self.assertEqual(result["cache_backend"], "Redis")
        self.assertEqual(result["similarity_threshold"], 0.85)
        self.assertEqual(result["database_engine"], "SQLite")
        self.assertTrue(str(result["database_url"]).startswith("sqlite+pysqlite:///"))
        self.assertEqual(result["python_version"], "3.14.0")
        self.assertEqual(result["semantic_sql_version"], "0.1.0")
        self.assertEqual(result["operating_system"], "TestOS-1")
        self.assertTrue(result["ollama_available"])
        self.assertTrue(result["redis_available"])
        ollama_get.assert_called_once_with(settings_service.OLLAMA_TAGS_URL, timeout=3)

    def test_reports_unavailable_runtime_services(self) -> None:
        cache = FakeSemanticCache()
        cache.backend_name = "InMemory"
        cache.redis_available = False

        with (
            patch.object(settings_service, "get_semantic_cache_service", return_value=cache),
            patch.object(
                settings_service.requests,
                "get",
                side_effect=settings_service.RequestException("connection refused"),
            ),
        ):
            result = settings_service.get_runtime_settings()

        self.assertEqual(result["cache_backend"], "InMemory")
        self.assertFalse(result["ollama_available"])
        self.assertFalse(result["redis_available"])


if __name__ == "__main__":
    unittest.main()
