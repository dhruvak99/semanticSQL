import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.model_management_service import ModelNotInstalledError, OllamaUnavailableError


class ModelManagementEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_get_model_management_state(self) -> None:
        with patch(
            "app.api.v1.endpoints.model_management.get_model_management_state",
            return_value={
                "active_model": "llama3.1:8b",
                "embedding_model": "all-MiniLM-L6-v2",
                "semantic_threshold": 0.9,
                "installed_models_count": 1,
                "models": [
                    {
                        "name": "llama3.1:8b",
                        "size": "4.9 GB",
                        "modified": "5 weeks ago",
                        "active": True,
                    }
                ],
            },
        ):
            response = self.client.get("/api/v1/model-management/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["active_model"], "llama3.1:8b")

    def test_updates_active_model(self) -> None:
        with patch(
            "app.api.v1.endpoints.model_management.update_active_model",
            return_value="mistral:latest",
        ):
            response = self.client.post(
                "/api/v1/model-management/active-model",
                json={"model": "mistral:latest"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "message": "Active model updated successfully.",
                "active_model": "mistral:latest",
            },
        )

    def test_returns_not_found_for_uninstalled_model(self) -> None:
        with patch(
            "app.api.v1.endpoints.model_management.update_active_model",
            side_effect=ModelNotInstalledError("Ollama model 'missing:model' is not installed."),
        ):
            response = self.client.post(
                "/api/v1/model-management/active-model",
                json={"model": "missing:model"},
            )

        self.assertEqual(response.status_code, 404)

    def test_returns_service_unavailable_when_ollama_is_down(self) -> None:
        with patch(
            "app.api.v1.endpoints.model_management.get_model_management_state",
            side_effect=OllamaUnavailableError("Ollama is not running."),
        ):
            response = self.client.get("/api/v1/model-management/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Ollama is not running.")


if __name__ == "__main__":
    unittest.main()
