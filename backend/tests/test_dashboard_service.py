import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services import dashboard_service, query_history_service
from app.services.dashboard_service import get_dashboard_metrics
from app.services.query_history_service import create_history_record


class DashboardServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def test_computes_dashboard_metrics_from_query_history(self) -> None:
        with (
            patch.object(query_history_service, "SessionLocal", self.session_local),
            patch.object(dashboard_service, "SessionLocal", self.session_local),
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

            dashboard = get_dashboard_metrics()

        self.assertEqual(dashboard["total_queries"], 3)
        self.assertEqual(dashboard["successful_queries"], 2)
        self.assertEqual(dashboard["failed_queries"], 1)
        self.assertEqual(dashboard["cache_hits"], 2)
        self.assertEqual(dashboard["cache_misses"], 1)
        self.assertEqual(dashboard["cache_hit_rate"], 66.7)
        self.assertEqual(dashboard["average_execution_time"], 0.051)
        self.assertEqual(dashboard["llm_queries"], 2)
        self.assertEqual(dashboard["rule_queries"], 1)
        self.assertEqual(dashboard["schema_mismatches"], 1)
        self.assertEqual(len(dashboard["query_volume_trend"]), 1)
        self.assertEqual(dashboard["recent_queries"][0]["natural_language_query"], "Show all suppliers")

    def test_empty_history_returns_zero_dashboard_metrics(self) -> None:
        with patch.object(dashboard_service, "SessionLocal", self.session_local):
            dashboard = get_dashboard_metrics()

        self.assertEqual(dashboard["total_queries"], 0)
        self.assertEqual(dashboard["cache_hit_rate"], 0.0)
        self.assertEqual(dashboard["average_execution_time"], 0.0)
        self.assertEqual(dashboard["recent_queries"], [])
        self.assertEqual(dashboard["query_volume_trend"], [])


if __name__ == "__main__":
    unittest.main()
