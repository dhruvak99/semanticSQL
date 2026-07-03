import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services import query_history_service, validation_analytics_service
from app.services.query_history_service import create_history_record
from app.services.validation_analytics_service import get_validation_analytics


class ValidationAnalyticsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def test_computes_validation_metrics_from_history(self) -> None:
        with (
            patch.object(query_history_service, "SessionLocal", self.session_local),
            patch.object(validation_analytics_service, "SessionLocal", self.session_local),
        ):
            create_history_record(
                natural_language_query="Show employees from Finance",
                generated_sql="SELECT * FROM employees WHERE department = 'Finance';",
                generation_mode="Rule",
                cache_status="Hit",
                validation_status="Valid",
                execution_time=0.1,
                rows_returned=3,
            )
            create_history_record(
                natural_language_query="Show all vendors",
                generated_sql="SELECT * FROM vendors;",
                generation_mode="LLM",
                cache_status="Miss",
                validation_status="Valid",
                execution_time=0.2,
                rows_returned=4,
            )
            create_history_record(
                natural_language_query="Show all suppliers",
                generated_sql="SCHEMA_MISMATCH",
                generation_mode="LLM",
                cache_status="Miss",
                validation_status="Invalid",
                execution_time=0.05,
                rows_returned=0,
            )
            create_history_record(
                natural_language_query="Show unknown column",
                generated_sql="SELECT blood_group FROM employees;",
                generation_mode="LLM",
                cache_status="Miss",
                validation_status="Invalid",
                execution_time=0.03,
                rows_returned=0,
            )
            analytics = get_validation_analytics()

        self.assertEqual(analytics["total_validated_queries"], 4)
        self.assertEqual(analytics["valid_queries"], 2)
        self.assertEqual(analytics["invalid_queries"], 2)
        self.assertEqual(analytics["validation_success_rate"], 50.0)
        self.assertEqual(analytics["schema_mismatch_count"], 1)
        self.assertEqual(analytics["cache_hit_count"], 1)
        self.assertEqual(analytics["cache_miss_count"], 3)
        self.assertEqual(len(analytics["validation_logs"]), 4)
        self.assertEqual(len(analytics["recent_failures"]), 2)
        self.assertEqual(analytics["recent_failures"][1]["failure_type"], "Schema Mismatch")
        self.assertEqual(analytics["recent_failures"][0]["failure_type"], "Validation Failure")

    def test_empty_history_returns_zero_metrics(self) -> None:
        with patch.object(validation_analytics_service, "SessionLocal", self.session_local):
            analytics = get_validation_analytics()

        self.assertEqual(analytics["total_validated_queries"], 0)
        self.assertEqual(analytics["validation_success_rate"], 0.0)
        self.assertEqual(analytics["schema_mismatch_count"], 0)
        self.assertEqual(analytics["validation_logs"], [])
        self.assertEqual(analytics["recent_failures"], [])


if __name__ == "__main__":
    unittest.main()
