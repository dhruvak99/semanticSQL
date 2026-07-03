import unittest
from unittest.mock import Mock, patch

from requests import RequestException

from app.services import model_management_service
from app.services.model_management_service import (
    ModelNotInstalledError,
    OllamaUnavailableError,
    get_model_management_state,
    update_active_model,
)
from app.services.model_runtime_state import get_active_model, set_active_model


class ModelManagementServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_model = get_active_model()
        set_active_model("llama3.1:8b")

    def tearDown(self) -> None:
        set_active_model(self.original_model)

    def test_lists_installed_models_and_runtime_configuration(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "models": [
                {
                    "name": "llama3.1:8b",
                    "size": 4920753328,
                    "modified_at": "2026-05-03T19:34:47.112804576+05:30",
                },
                {
                    "name": "mistral:latest",
                    "size": 4372824384,
                    "modified_at": "2026-05-14T16:08:41.43186663+05:30",
                },
            ]
        }

        with patch.object(model_management_service.requests, "get", return_value=response):
            state = get_model_management_state()

        self.assertEqual(state["active_model"], "llama3.1:8b")
        self.assertEqual(state["embedding_model"], "all-MiniLM-L6-v2")
        self.assertEqual(state["semantic_threshold"], 0.9)
        self.assertEqual(state["installed_models_count"], 2)
        active_model = next(model for model in state["models"] if model["name"] == "llama3.1:8b")
        self.assertTrue(active_model["active"])
        self.assertEqual(active_model["size"], "4.9 GB")

    def test_updates_active_model_without_restart(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "models": [
                {"name": "llama3.1:8b"},
                {"name": "mistral:latest"},
            ]
        }

        with patch.object(model_management_service.requests, "get", return_value=response):
            active_model = update_active_model("mistral:latest")

        self.assertEqual(active_model, "mistral:latest")
        self.assertEqual(get_active_model(), "mistral:latest")

    def test_rejects_model_that_is_not_installed(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"models": [{"name": "llama3.1:8b"}]}

        with patch.object(model_management_service.requests, "get", return_value=response):
            with self.assertRaises(ModelNotInstalledError):
                update_active_model("missing:model")

        self.assertEqual(get_active_model(), "llama3.1:8b")

    def test_reports_unavailable_ollama_runtime(self) -> None:
        with patch.object(
            model_management_service.requests,
            "get",
            side_effect=RequestException("connection refused"),
        ):
            with self.assertRaises(OllamaUnavailableError):
                get_model_management_state()


if __name__ == "__main__":
    unittest.main()
