import logging
import re
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError

from app.db.base import Base
from app.db.session import engine
from app.models import QueryHistory

logger = logging.getLogger(__name__)


class DatabaseErrorCode(StrEnum):
    UNSAFE_SQL = "unsafe_sql"
    INVALID_SQL = "invalid_sql"
    CONNECTION_FAILED = "connection_failed"
    EXECUTION_FAILED = "execution_failed"


class DatabaseServiceError(Exception):
    def __init__(self, message: str, code: DatabaseErrorCode) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


FORBIDDEN_SQL_KEYWORDS = {
    "ALTER",
    "CREATE",
    "DELETE",
    "DROP",
    "INSERT",
    "REPLACE",
    "TRUNCATE",
    "UPDATE",
}

FORBIDDEN_SELECT_PATTERNS = (
    r"\bINTO\s+(OUTFILE|DUMPFILE)\b",
    r"\bFOR\s+UPDATE\b",
    r"\bLOCK\s+IN\s+SHARE\s+MODE\b",
)

SAMPLE_EMPLOYEES = [
    (101, "David Wilson", "david.wilson@company.com", "Engineering", 75000.00, "2019-07-18"),
    (104, "Sarah Johnson", "sarah.johnson@company.com", "Finance", 88000.00, "2020-03-22"),
    (107, "Michael Brown", "michael.brown@company.com", "Finance", 95000.00, "2021-05-10"),
    (109, "Jessica Lee", "jessica.lee@company.com", "Finance", 72000.00, "2022-01-15"),
    (115, "Daniel Martinez", "daniel.martinez@company.com", "Operations", 68000.00, "2021-11-30"),
    (121, "Priya Raman", "priya.raman@company.com", "Human Resources", 54000.00, "2023-02-06"),
    (126, "Ava Thompson", "ava.thompson@company.com", "Engineering", 99000.00, "2020-09-14"),
    (131, "Noah Garcia", "noah.garcia@company.com", "Operations", 48000.00, "2022-04-03"),
]


def initialize_database() -> None:
    _ = QueryHistory
    try:
        Base.metadata.create_all(bind=engine)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS employees ("
                    "employee_id INTEGER PRIMARY KEY, "
                    "name VARCHAR(100) NOT NULL, "
                    "email VARCHAR(150) NOT NULL UNIQUE, "
                    "department VARCHAR(100) NOT NULL, "
                    "salary DECIMAL(12, 2) NOT NULL, "
                    "joining_date DATE NOT NULL"
                    ");"
                )
            )
            employee_count = connection.execute(text("SELECT COUNT(*) FROM employees;")).scalar_one()
            if employee_count == 0:
                connection.execute(
                    text(
                        "INSERT INTO employees "
                        "(employee_id, name, email, department, salary, joining_date) "
                        "VALUES "
                        "(:employee_id, :name, :email, :department, :salary, :joining_date)"
                    ),
                    [
                        {
                            "employee_id": employee_id,
                            "name": name,
                            "email": email,
                            "department": department,
                            "salary": salary,
                            "joining_date": joining_date,
                        }
                        for employee_id, name, email, department, salary, joining_date in SAMPLE_EMPLOYEES
                    ],
                )
                logger.info("Seeded employees table with %s sample records", len(SAMPLE_EMPLOYEES))
    except SQLAlchemyError:
        logger.exception("Database initialization failed")
        raise


def execute_query(sql: str) -> list[dict[str, str | int | float | bool | None]]:
    _ensure_read_only_sql(sql)

    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql))
            rows = [dict(row) for row in result.mappings().all()]
    except OperationalError as error:
        logger.exception("Database connection failed")
        raise DatabaseServiceError(
            "Database connection failed. Check DATABASE_URL and MySQL availability.",
            DatabaseErrorCode.CONNECTION_FAILED,
        ) from error
    except ProgrammingError as error:
        logger.exception("Invalid SQL generated")
        raise DatabaseServiceError(
            "Generated SQL is invalid for the configured database.",
            DatabaseErrorCode.INVALID_SQL,
        ) from error
    except SQLAlchemyError as error:
        logger.exception("Database execution failed")
        raise DatabaseServiceError(
            "Database query execution failed.",
            DatabaseErrorCode.EXECUTION_FAILED,
        ) from error

    return [_serialize_row(row) for row in rows]


def _ensure_read_only_sql(sql: str) -> None:
    normalized_sql = _normalize_sql(sql)
    if not normalized_sql:
        raise DatabaseServiceError("SQL statement is empty.", DatabaseErrorCode.INVALID_SQL)

    if not normalized_sql.upper().startswith("SELECT "):
        raise DatabaseServiceError(
            "Only read-only SELECT queries are allowed.",
            DatabaseErrorCode.UNSAFE_SQL,
        )

    if "--" in normalized_sql or "/*" in normalized_sql or "*/" in normalized_sql or "#" in normalized_sql:
        raise DatabaseServiceError(
            "SQL comments are not allowed.",
            DatabaseErrorCode.UNSAFE_SQL,
        )

    forbidden_tokens = {
        keyword
        for keyword in FORBIDDEN_SQL_KEYWORDS
        if re.search(rf"\b{keyword}\b", normalized_sql, re.IGNORECASE)
    }
    if forbidden_tokens:
        blocked = ", ".join(sorted(forbidden_tokens))
        raise DatabaseServiceError(
            f"Blocked unsafe SQL keyword(s): {blocked}.",
            DatabaseErrorCode.UNSAFE_SQL,
        )

    if any(re.search(pattern, normalized_sql, re.IGNORECASE) for pattern in FORBIDDEN_SELECT_PATTERNS):
        raise DatabaseServiceError(
            "The SELECT statement contains a write or lock clause.",
            DatabaseErrorCode.UNSAFE_SQL,
        )

    if normalized_sql.count(";") > 1 or (";" in normalized_sql and not normalized_sql.endswith(";")):
        raise DatabaseServiceError(
            "Multiple SQL statements are not allowed.",
            DatabaseErrorCode.UNSAFE_SQL,
        )


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().split())


def _serialize_row(row: dict[str, Any]) -> dict[str, str | int | float | bool | None]:
    return {key: _serialize_value(value) for key, value in row.items()}


def _serialize_value(value: Any) -> str | int | float | bool | None:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)
