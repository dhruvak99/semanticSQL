import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services import query_history_service, system_monitor_service
from app.services.query_history_service import create_history_record
from app.services.system_monitor_service import get_system_monitor_metrics


class SystemMonitorServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def test_computes_monitor_metrics_from_query_history(self) -> None:
        with (
            patch.object(query_history_service, "SessionLocal", self.session_local),
            patch.object(system_monitor_service, "SessionLocal", self.session_local),
        ):
            create_history_record(
                natural_language_query="Show employees from Finance",
                generated_sql="SELECT * FROM employees WHERE department = 'Finance';",
                generation_mode="Rule",
                cache_status="Hit",
                validation_status="Valid",
                execution_time=0.1,
                rows_returned=2,
            )
            create_history_record(
                natural_language_query="Highest rated vendor",
                generated_sql="SELECT * FROM vendors ORDER BY rating DESC LIMIT 1;",
                generation_mode="LLM",
                cache_status="Hit",
                validation_status="Valid",
                execution_time=0.05,
                rows_returned=1,
            )
            create_history_record(
                natural_language_query="Show all suppliers",
                generated_sql="SCHEMA_MISMATCH",
                generation_mode="LLM",
                cache_status="Miss",
                validation_status="Invalid",
                execution_time=0.003,
                rows_returned=0,
            )

            monitor = get_system_monitor_metrics()

        self.assertEqual(monitor["total_queries"], 3)
        self.assertEqual(monitor["successful_queries"], 2)
        self.assertEqual(monitor["failed_queries"], 1)
        self.assertEqual(monitor["cache_hits"], 2)
        self.assertEqual(monitor["cache_misses"], 1)
        self.assertEqual(monitor["cache_hit_rate"], 66.7)
        self.assertEqual(monitor["average_execution_time"], 0.051)
        self.assertEqual(monitor["llm_queries"], 2)
        self.assertEqual(monitor["rule_queries"], 1)
        self.assertEqual(monitor["schema_mismatches"], 1)
        self.assertEqual(monitor["recent_failures"][0]["failure_type"], "Schema Mismatch")
        self.assertEqual(monitor["recent_activity"][0]["generation_mode"], "LLM")
        self.assertEqual(len(monitor["query_volume_trend"]), 1)

    def test_empty_history_returns_zero_metrics(self) -> None:
        with patch.object(system_monitor_service, "SessionLocal", self.session_local):
            monitor = get_system_monitor_metrics()

        self.assertEqual(monitor["total_queries"], 0)
        self.assertEqual(monitor["cache_hit_rate"], 0.0)
        self.assertEqual(monitor["average_execution_time"], 0.0)
        self.assertEqual(monitor["recent_failures"], [])
        self.assertEqual(monitor["recent_activity"], [])
        self.assertEqual(monitor["query_volume_trend"], [])


if __name__ == "__main__":
    unittest.main()
