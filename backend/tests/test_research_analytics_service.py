import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services import query_history_service, research_analytics_service
from app.services.query_history_service import create_history_record
from app.services.research_analytics_service import get_research_analytics


class ResearchAnalyticsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def test_computes_research_analytics_from_query_history(self) -> None:
        with (
            patch.object(query_history_service, "SessionLocal", self.session_local),
            patch.object(research_analytics_service, "SessionLocal", self.session_local),
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

            analytics = get_research_analytics()

        self.assertEqual(analytics["total_queries"], 3)
        self.assertEqual(analytics["successful_queries"], 2)
        self.assertEqual(analytics["failed_queries"], 1)
        self.assertEqual(analytics["cache_hits"], 1)
        self.assertEqual(analytics["cache_misses"], 2)
        self.assertEqual(analytics["cache_hit_rate"], 33.3)
        self.assertEqual(analytics["average_execution_time"], 0.117)
        self.assertEqual(analytics["llm_queries"], 2)
        self.assertEqual(analytics["rule_queries"], 1)
        self.assertEqual(analytics["schema_mismatches"], 1)
        self.assertEqual(len(analytics["volume_trend"]), 1)
        self.assertEqual(analytics["recent_queries"][0]["generation_mode"], "LLM")

    def test_empty_history_returns_zero_research_analytics(self) -> None:
        with patch.object(research_analytics_service, "SessionLocal", self.session_local):
            analytics = get_research_analytics()

        self.assertEqual(analytics["total_queries"], 0)
        self.assertEqual(analytics["cache_hit_rate"], 0.0)
        self.assertEqual(analytics["average_execution_time"], 0.0)
        self.assertEqual(analytics["volume_trend"], [])
        self.assertEqual(analytics["recent_queries"], [])


if __name__ == "__main__":
    unittest.main()
