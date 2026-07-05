from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from benchmark import evaluate


@dataclass
class FakeResponse:
    status_code: int
    payload: dict[str, Any] | None = None
    text: str = ""
    closed: bool = False

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    @property
    def content(self) -> bytes:
        return str(self.payload or self.text).encode("utf-8")

    def json(self) -> dict[str, Any]:
        if self.payload is None:
            raise ValueError("no json")
        return self.payload

    def close(self) -> None:
        self.closed = True


class FakeSession:
    def __init__(self, post_response: FakeResponse | None = None, get_response: FakeResponse | None = None) -> None:
        self.post_response = post_response or FakeResponse(200, {})
        self.get_response = get_response or FakeResponse(200, {"status": "ok"})
        self.posts: list[dict[str, Any]] = []
        self.closed = False

    def get(self, *_args: Any, **_kwargs: Any) -> FakeResponse:
        return self.get_response

    def post(self, *_args: Any, **kwargs: Any) -> FakeResponse:
        self.posts.append(kwargs.get("json", {}))
        return self.post_response

    def close(self) -> None:
        self.closed = True


def test_backend_unavailable_returns_false() -> None:
    class FailingSession:
        def get(self, *_args: Any, **_kwargs: Any) -> FakeResponse:
            raise evaluate.requests.ConnectionError("offline")

    assert evaluate._backend_available(FailingSession(), "http://localhost:8000", 1) is False  # type: ignore[arg-type]


def test_sql_equivalence_uses_sqlglot_normalization() -> None:
    assert evaluate._sql_equivalent("SELECT name FROM employees;", "select name from employees")


def test_result_equivalence_ignores_order_without_order_by() -> None:
    expected = [{"id": 1, "score": 1.0000001}, {"id": 2, "score": None}]
    actual = [{"score": None, "id": 2}, {"score": 1.0000002, "id": 1}]

    assert evaluate._result_equivalent("SELECT id, score FROM employees;", expected, actual)


def test_result_equivalence_respects_order_by() -> None:
    expected = [{"id": 1}, {"id": 2}]
    actual = [{"id": 2}, {"id": 1}]

    assert not evaluate._result_equivalent("SELECT id FROM employees ORDER BY id;", expected, actual)


def test_summary_metrics_include_cache_and_generation_modes() -> None:
    results = [
        _result("functional", True, True, "Rule", 10.0),
        _result("semantic", False, True, "LLM", 20.0),
        _result("invalid", True, False, "LLM", 30.0),
    ]

    summary = evaluate._build_summary(results)

    assert summary["overall_accuracy"] == 66.667
    assert summary["cache_hit_rate"] == 66.667
    assert summary["generation_mode_distribution"] == {"LLM": 2, "Rule": 1}
    assert summary["average_execution_time_ms"] == 20.0


def test_cache_comparison_metrics() -> None:
    cold = [_result("functional", True, False, "Rule", 100.0)]
    warm = [_result("functional", True, True, "Rule", 40.0)]

    comparison = evaluate._build_cache_comparison(cold, warm)

    assert comparison["latency_improvement_percent"] == 60.0
    assert comparison["cache_hit_rate_improvement"] == 100.0


def test_evaluate_query_successful_valid_query(monkeypatch: Any) -> None:
    executor = FakeExpectedExecutor([{"id": 1}], None)
    response = FakeResponse(
        200,
        {
            "generated_sql": "SELECT id FROM employees;",
            "validation_status": "valid",
            "validation_errors": [],
            "cache_hit": False,
            "similarity_score": 0.0,
            "generation_mode": "Rule",
            "rows_returned": 1,
            "execution_time": 0.01,
            "results": [{"id": 1}],
        },
    )
    session = FakeSession(
        response
    )
    query = {
        "id": "F0001",
        "dataset": "functional",
        "category": "SELECT",
        "difficulty": "easy",
        "complexity_score": 1,
        "natural_language_query": "Show employee IDs.",
        "expected_sql": "SELECT id FROM employees;",
    }

    result = evaluate._evaluate_query("cold_cache", session, "http://backend", 1, "1.0.0", executor, query, _NullLogger())

    assert result["passed"] is True
    assert result["result_equivalent"] is True
    assert session.posts == [{"query": "Show employee IDs."}]
    assert response.closed is True


def test_invalid_query_passes_when_backend_rejects() -> None:
    session = FakeSession(
        FakeResponse(
            200,
            {
                "generated_sql": "SCHEMA_MISMATCH",
                "validation_status": "invalid",
                "validation_errors": ["Requested table or column does not exist."],
                "cache_hit": False,
                "similarity_score": 0.0,
                "generation_mode": "LLM",
                "rows_returned": 0,
                "execution_time": 0.01,
                "results": [],
            },
        )
    )
    query = {
        "id": "I0001",
        "dataset": "invalid",
        "natural_language_query": "Show missing records.",
        "expected_sql": "SELECT * FROM missing_table;",
    }

    result = evaluate._evaluate_query("cold_cache", session, "http://backend", 1, "1.0.0", FakeExpectedExecutor([], None), query, _NullLogger())

    assert result["passed"] is True


def test_read_only_expected_sql_enforcement(monkeypatch: Any) -> None:
    executor = FakeExpectedExecutor([], None)
    session = FakeSession(FakeResponse(500, {"detail": "error"}))
    query = {
        "id": "F0002",
        "dataset": "functional",
        "natural_language_query": "Delete employees.",
        "expected_sql": "DELETE FROM employees;",
    }

    result = evaluate._evaluate_query("cold_cache", session, "http://backend", 1, "1.0.0", executor, query, _NullLogger())

    assert executor.calls == []
    assert result["passed"] is False
    assert result["failure_reason"] == "Expected SQL skipped because it is not a SELECT statement."


def test_manifest_finalization_uses_unknown_platform_fallback_and_writes_file(tmp_path: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(evaluate.platform, "platform", lambda: (_ for _ in ()).throw(OSError("too many files")))
    monkeypatch.setattr(evaluate.platform, "python_version", lambda: (_ for _ in ()).throw(OSError("too many files")))
    monkeypatch.setattr(evaluate.platform, "processor", lambda: (_ for _ in ()).throw(OSError("too many files")))
    manifest = evaluate._build_experiment_manifest(
        "experiment",
        {"benchmark_version": "1.0.0", "database_name": "db", "database_path": "db.sqlite", "database_engine": "SQLite"},
        {},
        "2026-01-01T00:00:00+00:00",
        "http://backend",
        1,
        {"successful_queries": 1, "failed_queries": 0},
    )

    evaluate._write_json(tmp_path / "experiment_manifest.json", manifest)
    written = evaluate._read_json(tmp_path / "experiment_manifest.json")

    assert written["platform"] == "unknown"
    assert written["python_version"] == "unknown"
    assert written["processor"] == "unknown"


def test_session_and_logger_resources_are_explicitly_closed(tmp_path: Any) -> None:
    session = FakeSession()
    logger = evaluate._configure_logging(tmp_path)

    session.close()
    evaluate._close_logger(logger)

    assert session.closed is True
    assert logger.handlers == []


def _result(dataset: str, passed: bool, cache_hit: bool, generation_mode: str, latency: float) -> dict[str, Any]:
    return {
        "dataset": dataset,
        "passed": passed,
        "cache_hit": cache_hit,
        "generation_mode": generation_mode,
        "execution_time_ms": latency,
        "validation_status": "valid" if passed else "invalid",
        "sql_equivalent": passed,
        "result_equivalent": passed,
    }


class _NullLogger:
    def warning(self, *_args: Any, **_kwargs: Any) -> None:
        return None


class FakeExpectedExecutor:
    def __init__(self, rows: list[dict[str, Any]], error: str | None) -> None:
        self.rows = rows
        self.error = error
        self.calls: list[str] = []

    def execute(self, sql: str) -> tuple[list[dict[str, Any]], str | None]:
        self.calls.append(sql)
        return self.rows, self.error
