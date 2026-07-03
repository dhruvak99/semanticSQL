import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class SchemaEndpointTests(unittest.TestCase):
    def test_schema_endpoint_returns_database_metadata(self) -> None:
        with patch(
            "app.api.v1.endpoints.schema.get_database_schema",
            return_value={
                "table_count": 1,
                "column_count": 2,
                "tables": [
                    {
                        "name": "employees",
                        "column_count": 2,
                        "columns": [
                            {"name": "employee_id", "type": "INTEGER", "primary_key": True},
                            {"name": "name", "type": "TEXT", "primary_key": False},
                        ],
                    }
                ],
            },
        ):
            client = TestClient(app)
            response = client.get("/api/v1/schema/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["table_count"], 1)
        self.assertTrue(response.json()["tables"][0]["columns"][0]["primary_key"])


if __name__ == "__main__":
    unittest.main()
