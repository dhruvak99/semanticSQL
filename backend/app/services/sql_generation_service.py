import re
from dataclasses import dataclass
from enum import StrEnum


class QueryType(StrEnum):
    LIST_DEPARTMENTS = "list_departments"
    SALARY_FILTER = "salary_filter"
    COUNT_BY_DEPARTMENT = "count_by_department"
    DEPARTMENT_FILTER = "department_filter"
    CREATE_EMPLOYEE_TABLE = "create_employee_table"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SQLGenerationResult:
    sql: str
    query_type: QueryType


def generate_sql(natural_language_query: str) -> SQLGenerationResult:
    query = natural_language_query.strip()
    normalized_query = " ".join(query.lower().split())

    if normalized_query == "list all departments":
        return SQLGenerationResult(
            sql="SELECT DISTINCT department FROM employees;",
            query_type=QueryType.LIST_DEPARTMENTS,
        )

    salary_match = re.search(r"show employees with salary greater than (\d+(?:\.\d+)?)", normalized_query)
    if salary_match:
        salary_threshold = salary_match.group(1)
        return SQLGenerationResult(
            sql=f"SELECT * FROM employees WHERE salary > {salary_threshold};",
            query_type=QueryType.SALARY_FILTER,
        )

    if normalized_query == "count employees in each department":
        return SQLGenerationResult(
            sql=(
                "SELECT department, COUNT(*) AS employee_count\n"
                "FROM employees\n"
                "GROUP BY department;"
            ),
            query_type=QueryType.COUNT_BY_DEPARTMENT,
        )

    department_match = re.search(
        r"show employees from (?:department )?([a-zA-Z][a-zA-Z\s_-]*)$",
        query,
        re.IGNORECASE,
    )
    if department_match:
        department = department_match.group(1).strip()
        escaped_department = department.replace("'", "''")
        return SQLGenerationResult(
            sql=(
                "SELECT * FROM employees\n"
                f"WHERE department = '{escaped_department}';"
            ),
            query_type=QueryType.DEPARTMENT_FILTER,
        )

    create_table_match = re.search(
        r"create employee table with (?P<columns>[a-zA-Z0-9_,\s]+)$",
        query,
        re.IGNORECASE,
    )
    if create_table_match:
        columns = [
            column.strip().lower().replace(" ", "_")
            for column in create_table_match.group("columns").split(",")
            if column.strip()
        ]
        return SQLGenerationResult(
            sql=_build_create_employee_table_sql(columns),
            query_type=QueryType.CREATE_EMPLOYEE_TABLE,
        )

    return SQLGenerationResult(
        sql="-- Unable to generate SQL for the provided natural language query.",
        query_type=QueryType.UNKNOWN,
    )


def _build_create_employee_table_sql(columns: list[str]) -> str:
    if not columns:
        columns = ["id", "name", "salary"]

    column_definitions = [_column_definition(column) for column in columns]
    return "CREATE TABLE employees (\n  " + ",\n  ".join(column_definitions) + "\n);"


def _column_definition(column: str) -> str:
    if column in {"id", "employee_id"}:
        return f"{column} INT PRIMARY KEY AUTO_INCREMENT"
    if column in {"name", "employee_name"}:
        return f"{column} VARCHAR(100) NOT NULL"
    if column == "salary":
        return "salary DECIMAL(12, 2) NOT NULL"
    if column in {"department", "dept"}:
        return f"{column} VARCHAR(100)"
    if column in {"email", "email_address"}:
        return f"{column} VARCHAR(150)"
    if column.endswith("_date") or column in {"joining_date", "hire_date"}:
        return f"{column} DATE"
    return f"{column} VARCHAR(255)"
