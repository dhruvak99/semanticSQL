import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class SystemMonitorEndpointTests(unittest.TestCase):
    def test_system_monitor_endpoint_returns_application_metrics(self) -> None:
        with patch(
            "app.api.v1.endpoints.system_monitor.get_system_monitor_metrics",
            return_value={
                "total_queries": 10,
                "successful_queries": 6,
                "failed_queries": 4,
                "cache_hits": 6,
                "cache_misses": 4,
                "cache_hit_rate": 60.0,
                "average_execution_time": 0.051,
                "schema_mismatches": 4,
                "llm_queries": 8,
                "rule_queries": 2,
                "recent_failures": [],
                "recent_activity": [],
                "query_volume_trend": [{"date": "2026-06-08", "count": 10}],
            },
        ):
            client = TestClient(app)
            response = client.get("/api/v1/system-monitor/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_queries"], 10)
        self.assertEqual(response.json()["cache_hit_rate"], 60.0)
        self.assertEqual(response.json()["llm_queries"], 8)


if __name__ == "__main__":
    unittest.main()
