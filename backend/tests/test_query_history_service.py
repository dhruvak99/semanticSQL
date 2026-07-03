import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.query_history import QueryHistory
from app.services import query_history_service
from app.services.query_history_service import create_history_record, list_history_records


class QueryHistoryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def test_creates_and_lists_history_records_newest_first(self) -> None:
        with patch.object(query_history_service, "SessionLocal", self.session_local):
            first = create_history_record(
                natural_language_query="Show employees from Finance",
                generated_sql="SELECT * FROM employees WHERE department = 'Finance';",
                generation_mode="Rule",
                cache_status="Miss",
                validation_status="Valid",
                execution_time=0.12,
                rows_returned=3,
            )
            second = create_history_record(
                natural_language_query="Show all suppliers",
                generated_sql="SCHEMA_MISMATCH",
                generation_mode="LLM",
                cache_status="Miss",
                validation_status="Invalid",
                execution_time=0.01,
                rows_returned=0,
            )
            records = list_history_records()

        self.assertIsInstance(first, QueryHistory)
        self.assertEqual(second.id, 2)
        self.assertEqual([record["id"] for record in records], [2, 1])
        self.assertEqual(records[0]["natural_language_query"], "Show all suppliers")
        self.assertEqual(records[0]["generated_sql"], "SCHEMA_MISMATCH")
        self.assertEqual(records[0]["generation_mode"], "LLM")
        self.assertEqual(records[0]["cache_status"], "Miss")
        self.assertEqual(records[0]["validation_status"], "Invalid")
        self.assertEqual(records[0]["rows_returned"], 0)
        self.assertIn("created_at", records[0])

    def test_normalizes_generation_mode_when_storing_and_returning_records(self) -> None:
        with patch.object(query_history_service, "SessionLocal", self.session_local):
            legacy_mode = "L" + "lm"
            record = create_history_record(
                natural_language_query="Show all vendors",
                generated_sql="SELECT * FROM vendors;",
                generation_mode=legacy_mode,
                cache_status="Miss",
                validation_status="Valid",
                execution_time=0.1,
                rows_returned=4,
            )
            record.generation_mode = legacy_mode
            with self.session_local() as session:
                stored_record = session.get(QueryHistory, record.id)
                stored_record.generation_mode = legacy_mode
                session.commit()
            records = list_history_records()

        self.assertEqual(records[0]["generation_mode"], "LLM")


if __name__ == "__main__":
    unittest.main()
