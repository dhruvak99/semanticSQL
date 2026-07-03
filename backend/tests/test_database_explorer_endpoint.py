import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.database_explorer_service import DatabaseExplorerError


class DatabaseExplorerEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_tables_endpoint_returns_row_counts(self) -> None:
        with patch(
            "app.api.v1.endpoints.database.list_database_tables",
            return_value={"tables": [{"name": "vendors", "row_count": 4}]},
        ):
            response = self.client.get("/api/v1/database/tables")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"tables": [{"name": "vendors", "row_count": 4}]})

    def test_table_endpoint_returns_paginated_rows(self) -> None:
        with patch(
            "app.api.v1.endpoints.database.get_table_data",
            return_value={
                "table_name": "vendors",
                "columns": ["id", "vendor_name"],
                "rows": [[1, "Dell"]],
                "total_rows": 1,
                "page": 1,
                "page_size": 20,
            },
        ) as get_table_data_mock:
            response = self.client.get("/api/v1/database/table/vendors?page=1&page_size=20")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rows"], [[1, "Dell"]])
        get_table_data_mock.assert_called_once_with("vendors", page=1, page_size=20)

    def test_unknown_table_returns_not_found(self) -> None:
        with patch(
            "app.api.v1.endpoints.database.get_table_data",
            side_effect=DatabaseExplorerError("Table 'missing' does not exist"),
        ):
            response = self.client.get("/api/v1/database/table/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Table 'missing' does not exist")


if __name__ == "__main__":
    unittest.main()
