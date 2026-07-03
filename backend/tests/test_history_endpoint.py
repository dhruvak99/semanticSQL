import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class HistoryEndpointTests(unittest.TestCase):
    def test_history_endpoint_returns_records(self) -> None:
        with patch(
            "app.api.v1.endpoints.history.list_history_records",
            return_value=[
                {
                    "id": 1,
                    "natural_language_query": "Show employees from Finance",
                    "generated_sql": "SELECT * FROM employees WHERE department = 'Finance';",
                    "generation_mode": "Rule",
                    "cache_status": "Miss",
                    "validation_status": "Valid",
                    "execution_time": 0.25,
                    "rows_returned": 3,
                    "created_at": "2026-06-08T10:00:00+00:00",
                }
            ],
        ):
            client = TestClient(app)
            response = client.get("/api/v1/history/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["natural_language_query"], "Show employees from Finance")

    def test_history_analytics_endpoint_returns_metrics(self) -> None:
        with patch(
            "app.api.v1.endpoints.history.get_query_analytics",
            return_value={
                "total_queries": 10,
                "successful_queries": 6,
                "failed_queries": 4,
                "cache_hits": 6,
                "cache_misses": 4,
                "cache_hit_rate": 60.0,
                "average_execution_time": 0.051,
                "rule_generation_count": 2,
                "llm_generation_count": 8,
                "schema_mismatch_count": 4,
                "volume_trend": [],
                "recent_queries": [],
            },
        ):
            client = TestClient(app)
            response = client.get("/api/v1/history/analytics")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cache_hit_rate"], 60.0)
        self.assertEqual(response.json()["schema_mismatch_count"], 4)

    def test_validation_analytics_endpoint_returns_metrics(self) -> None:
        with patch(
            "app.api.v1.endpoints.history.get_validation_analytics",
            return_value={
                "total_validated_queries": 10,
                "valid_queries": 6,
                "invalid_queries": 4,
                "validation_success_rate": 60.0,
                "schema_mismatch_count": 4,
                "cache_hit_count": 6,
                "cache_miss_count": 4,
                "validation_logs": [],
                "recent_failures": [
                    {
                        "natural_language_query": "Show employee blood group",
                        "generated_sql": "SCHEMA_MISMATCH",
                        "validation_status": "Invalid",
                        "failure_type": "Schema Mismatch",
                        "created_at": "2026-06-08T13:50:00",
                    }
                ],
            },
        ):
            client = TestClient(app)
            response = client.get("/api/v1/history/validation-analytics")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["validation_success_rate"], 60.0)
        self.assertEqual(response.json()["recent_failures"][0]["failure_type"], "Schema Mismatch")


if __name__ == "__main__":
    unittest.main()
