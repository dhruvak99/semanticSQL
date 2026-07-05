from __future__ import annotations

import argparse
import json
import logging
import math
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import sqlglot
from requests import Session
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"
QUERY_ENDPOINT = f"{API_PREFIX}/query/process"
SETTINGS_ENDPOINT = f"{API_PREFIX}/settings/"
CACHE_ENDPOINT = f"{API_PREFIX}/cache/"
HTTP_TIMEOUT_SECONDS = 120
FLOAT_PRECISION = 6


def main() -> None:
    parser = argparse.ArgumentParser(description="Run end-to-end SemanticSQL benchmark evaluation.")
    parser.add_argument("--benchmark-dir", default="benchmark", help="Directory containing manifest.json and datasets.")
    parser.add_argument("--results-dir", default="results", help="Directory where experiment outputs are written.")
    parser.add_argument("--experiment-name", default="SemanticSQL Benchmark Evaluation")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL, help="Running FastAPI backend base URL.")
    parser.add_argument("--timeout", type=float, default=HTTP_TIMEOUT_SECONDS, help="Per-request timeout in seconds.")
    args = parser.parse_args()

    benchmark_dir = Path(args.benchmark_dir)
    results_dir = Path(args.results_dir)
    session = requests.Session()
    logger: logging.Logger | None = None
    expected_executor: ExpectedSqlExecutor | None = None
    backend_url = args.backend_url.rstrip("/")

    try:
        if not _backend_available(session, backend_url, args.timeout):
            print(f"SemanticSQL backend is unreachable at {backend_url}. Start the backend and rerun evaluation.")
            return

        manifest = _read_json(benchmark_dir / "manifest.json")
        datasets = _load_datasets(benchmark_dir)
        settings = _fetch_backend_settings(session, backend_url, args.timeout)
        logger = _configure_logging(results_dir)
        logger.info("Starting SemanticSQL benchmark evaluation against %s", backend_url)

        if not _clear_semantic_cache(logger):
            logger.warning("Semantic cache could not be cleared through the existing service.")

        timestamp = datetime.now(UTC).isoformat()
        expected_executor = ExpectedSqlExecutor(manifest["database_path"])
        cold_results = _run_experiment(
            name="cold_cache",
            session=session,
            backend_url=backend_url,
            timeout=args.timeout,
            benchmark_version=manifest["benchmark_version"],
            expected_executor=expected_executor,
            queries=datasets,
            logger=logger,
        )
        warm_results = _run_experiment(
            name="warm_cache",
            session=session,
            backend_url=backend_url,
            timeout=args.timeout,
            benchmark_version=manifest["benchmark_version"],
            expected_executor=expected_executor,
            queries=datasets,
            logger=logger,
        )
    finally:
        session.close()
        if expected_executor is not None:
            expected_executor.close()

    all_results = cold_results + warm_results
    evaluation_summary = _build_summary(all_results)
    cold_summary = _build_summary(cold_results)
    warm_summary = _build_summary(warm_results)
    cache_comparison = _build_cache_comparison(cold_results, warm_results)
    evaluation_metrics = {
        "benchmark_version": manifest["benchmark_version"],
        "experiment_name": args.experiment_name,
        "execution_timestamp": timestamp,
        "overall": evaluation_summary,
        "cold_cache": cold_summary,
        "warm_cache": warm_summary,
        "cache_comparison": cache_comparison,
    }
    if logger is not None:
        logger.info("Evaluation execution complete: %s", json.dumps(evaluation_summary, sort_keys=True))
        logger.info("Closing execution resources before writing manifests.")
        _close_logger(logger)

    experiment_manifest = _build_experiment_manifest(
        args.experiment_name,
        manifest,
        settings,
        timestamp,
        backend_url,
        len(datasets),
        evaluation_summary,
    )

    _write_result_files(
        results_dir,
        manifest["benchmark_version"],
        args.experiment_name,
        timestamp,
        all_results,
        cold_results,
        warm_results,
        evaluation_summary,
        evaluation_metrics,
        cache_comparison,
        experiment_manifest,
    )


def _backend_available(session: Session, backend_url: str, timeout: float) -> bool:
    response = None
    try:
        response = session.get(f"{backend_url}/health", timeout=timeout)
        return response.status_code < 500
    except requests.RequestException:
        return False
    finally:
        if response is not None:
            response.close()


def _fetch_backend_settings(session: Session, backend_url: str, timeout: float) -> dict[str, Any]:
    response = None
    try:
        response = session.get(f"{backend_url}{SETTINGS_ENDPOINT}", timeout=timeout)
        if response.ok:
            return response.json()
    except (requests.RequestException, ValueError):
        pass
    finally:
        if response is not None:
            response.close()
    return {}


def _clear_semantic_cache(logger: logging.Logger) -> bool:
    try:
        backend_path = Path(__file__).resolve().parents[1] / "backend"
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        from app.services.semantic_cache_service import get_semantic_cache_service  # type: ignore[import-not-found]

        service = get_semantic_cache_service()
        service.clear()
        logger.info("Semantic cache cleared through existing service backend=%s", service.backend_name)
        return True
    except Exception as error:  # pragma: no cover - defensive around optional backend import
        logger.warning("Unable to clear semantic cache through existing service: %s", error)
        return False


def _run_experiment(
    name: str,
    session: Session,
    backend_url: str,
    timeout: float,
    benchmark_version: str,
    expected_executor: ExpectedSqlExecutor,
    queries: list[dict[str, Any]],
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    start_time = time.perf_counter()
    for index, query in enumerate(queries, start=1):
        result = _evaluate_query(
            experiment_mode=name,
            session=session,
            backend_url=backend_url,
            timeout=timeout,
            benchmark_version=benchmark_version,
            expected_executor=expected_executor,
            query=query,
            logger=logger,
        )
        results.append(result)
        _print_progress(name, index, len(queries), start_time, query["dataset"])
    print()
    return results


def _evaluate_query(
    experiment_mode: str,
    session: Session,
    backend_url: str,
    timeout: float,
    benchmark_version: str,
    expected_executor: ExpectedSqlExecutor,
    query: dict[str, Any],
    logger: logging.Logger,
) -> dict[str, Any]:
    timestamp = datetime.now(UTC).isoformat()
    expected_sql = query["expected_sql"]
    expected_select = _is_select_sql(expected_sql)
    expected_rows: list[dict[str, Any]] | None = None
    expected_error: str | None = None
    if query["dataset"] != "invalid" and expected_select:
        expected_rows, expected_error = expected_executor.execute(expected_sql)
    elif query["dataset"] != "invalid":
        expected_error = "Expected SQL skipped because it is not a SELECT statement."

    started = time.perf_counter()
    http_status = 0
    response_payload: dict[str, Any] = {}
    backend_error: str | None = None
    response_size = 0
    response = None
    try:
        response = session.post(
            f"{backend_url}{QUERY_ENDPOINT}",
            json={"query": query["natural_language_query"]},
            timeout=timeout,
        )
        http_status = response.status_code
        response_size = len(response.content or b"")
        try:
            response_payload = response.json()
        except ValueError:
            backend_error = response.text
    except requests.RequestException as error:
        backend_error = str(error)
    finally:
        if response is not None:
            response.close()

    elapsed_ms = (time.perf_counter() - started) * 1000
    generated_sql = _payload_string(response_payload, "generated_sql")
    corrected_sql = _payload_optional_string(response_payload, "corrected_sql")
    executed_sql = _payload_optional_string(response_payload, "executed_sql")
    validation_status = str(response_payload.get("validation_status", "error" if backend_error else "unknown"))
    validation_errors = _payload_list(response_payload, "validation_errors")
    cache_hit = bool(response_payload.get("cache_hit", False))
    similarity_score = _payload_float(response_payload, "similarity_score")
    generation_mode = _payload_optional_string(response_payload, "generation_mode")
    rows_returned = _payload_int(response_payload, "rows_returned")
    backend_results = response_payload.get("results", [])
    if not isinstance(backend_results, list):
        backend_results = []

    sql_equivalent = _sql_equivalent(expected_sql, generated_sql) if generated_sql else False
    result_equivalent = False
    failure_reason = None
    if query["dataset"] == "invalid":
        passed = http_status >= 400 or validation_status.lower() == "invalid" or bool(validation_errors)
        result_equivalent = passed
        if not passed:
            failure_reason = "Invalid benchmark query was not rejected."
    else:
        if expected_error:
            passed = False
            failure_reason = expected_error
        else:
            result_equivalent = _result_equivalent(expected_sql, expected_rows or [], backend_results)
            passed = http_status < 400 and validation_status.lower() == "valid" and result_equivalent
            if not passed:
                failure_reason = _valid_failure_reason(http_status, validation_status, result_equivalent, backend_error)

    execution_time_ms = _payload_float(response_payload, "execution_time")
    if execution_time_ms is not None:
        execution_time_ms *= 1000
    else:
        execution_time_ms = elapsed_ms

    result = {
        "benchmark_version": benchmark_version,
        "experiment_mode": experiment_mode,
        "query_id": query["id"],
        "dataset": query["dataset"],
        "category": query.get("category"),
        "difficulty": query.get("difficulty"),
        "complexity_score": query.get("complexity_score"),
        "natural_language_query": query["natural_language_query"],
        "expected_sql": expected_sql,
        "generated_sql": generated_sql,
        "corrected_sql": corrected_sql,
        "executed_sql": executed_sql,
        "validation_status": validation_status,
        "validation_errors": validation_errors,
        "cache_hit": cache_hit,
        "similarity_score": similarity_score,
        "generation_mode": generation_mode,
        "rows_returned": rows_returned,
        "execution_time_ms": round(execution_time_ms, 3),
        "http_status": http_status,
        "passed": passed,
        "failure_reason": failure_reason,
        "backend_error": backend_error,
        "sql_equivalent": sql_equivalent,
        "result_equivalent": result_equivalent,
        "response_size_bytes": response_size,
        "timestamp": timestamp,
    }
    if backend_error or failure_reason:
        logger.warning("Query %s failed: backend=%s reason=%s", query["id"], backend_error, failure_reason)
    return result


class ExpectedSqlExecutor:
    def __init__(self, database_path: str) -> None:
        self._engine: Engine = create_engine(f"sqlite+pysqlite:///{database_path}")

    def execute(self, sql: str) -> tuple[list[dict[str, Any]] | None, str | None]:
        if not _is_select_sql(sql):
            return None, "Expected SQL is not a SELECT statement."
        try:
            with self._engine.connect() as connection:
                result = connection.execute(text(sql))
                try:
                    rows = result.mappings().all()
                    return [dict(row) for row in rows], None
                finally:
                    result.close()
        except SQLAlchemyError as error:
            return None, str(error)

    def close(self) -> None:
        self._engine.dispose()


def _is_select_sql(sql: str) -> bool:
    try:
        expression = sqlglot.parse_one(sql, read="sqlite")
    except sqlglot.errors.ParseError:
        return False
    return expression is not None and expression.key.upper() == "SELECT"


def _sql_equivalent(expected_sql: str, generated_sql: str) -> bool:
    try:
        expected = sqlglot.parse_one(expected_sql, read="sqlite").sql(dialect="sqlite", normalize=True)
        generated = sqlglot.parse_one(generated_sql, read="sqlite").sql(dialect="sqlite", normalize=True)
    except Exception:
        return False
    return " ".join(expected.split()).lower() == " ".join(generated.split()).lower()


def _result_equivalent(expected_sql: str, expected_rows: list[dict[str, Any]], actual_rows: list[Any]) -> bool:
    normalized_expected = [_normalize_row(row) for row in expected_rows]
    normalized_actual = [_normalize_row(row) for row in actual_rows if isinstance(row, dict)]
    if not _has_order_by(expected_sql):
        normalized_expected = sorted(normalized_expected, key=_stable_json)
        normalized_actual = sorted(normalized_actual, key=_stable_json)
    return normalized_expected == normalized_actual


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key): _normalize_value(value) for key, value in sorted(row.items(), key=lambda item: str(item[0]))}


def _normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return round(value, FLOAT_PRECISION)
    if isinstance(value, int):
        return int(value)
    return str(value)


def _has_order_by(sql: str) -> bool:
    try:
        expression = sqlglot.parse_one(sql, read="sqlite")
    except sqlglot.errors.ParseError:
        return False
    return bool(list(expression.find_all(sqlglot.exp.Order)))


def _build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for result in results if result["passed"])
    valid_results = [result for result in results if result["dataset"] != "invalid"]
    invalid_results = [result for result in results if result["dataset"] == "invalid"]
    latencies = [float(result["execution_time_ms"]) for result in results]
    similarity_scores = [
        float(result["similarity_score"])
        for result in results
        if result.get("similarity_score") is not None
    ]
    cache_hits = sum(1 for result in results if result["cache_hit"])
    generation_modes = Counter(str(result.get("generation_mode") or "unknown") for result in results)

    return {
        "total_queries": total,
        "successful_queries": passed,
        "failed_queries": total - passed,
        "overall_accuracy": _percent(passed, total),
        "functional_accuracy": _dataset_accuracy(results, "functional"),
        "semantic_accuracy": _dataset_accuracy(results, "semantic"),
        "invalid_detection_accuracy": _dataset_accuracy(results, "invalid"),
        "sql_equivalence_rate": _percent(sum(1 for result in valid_results if result["sql_equivalent"]), len(valid_results)),
        "result_equivalence_rate": _percent(sum(1 for result in valid_results if result["result_equivalent"]), len(valid_results)),
        "accuracy_by_category": _accuracy_by_field(results, "category"),
        "accuracy_by_difficulty": _accuracy_by_field(results, "difficulty"),
        "dataset_analysis": _accuracy_by_field(results, "dataset"),
        "cache_hit_rate": _percent(cache_hits, total),
        "cache_miss_rate": _percent(total - cache_hits, total),
        "average_execution_time_ms": _round_stat(statistics.mean(latencies) if latencies else 0),
        "median_execution_time_ms": _round_stat(statistics.median(latencies) if latencies else 0),
        "minimum_execution_time_ms": _round_stat(min(latencies) if latencies else 0),
        "maximum_execution_time_ms": _round_stat(max(latencies) if latencies else 0),
        "p95_execution_time_ms": _round_stat(_percentile(latencies, 95)),
        "standard_deviation_execution_time_ms": _round_stat(statistics.pstdev(latencies) if len(latencies) > 1 else 0),
        "validation_failure_rate": _percent(sum(1 for result in results if str(result["validation_status"]).lower() != "valid"), total),
        "average_similarity_score": _round_stat(statistics.mean(similarity_scores) if similarity_scores else 0),
        "generation_mode_distribution": dict(sorted(generation_modes.items())),
    }


def _build_cache_comparison(cold_results: list[dict[str, Any]], warm_results: list[dict[str, Any]]) -> dict[str, Any]:
    cold_summary = _build_summary(cold_results)
    warm_summary = _build_summary(warm_results)
    hit_latencies = [float(result["execution_time_ms"]) for result in cold_results + warm_results if result["cache_hit"]]
    miss_latencies = [float(result["execution_time_ms"]) for result in cold_results + warm_results if not result["cache_hit"]]
    cold_latency = cold_summary["average_execution_time_ms"]
    warm_latency = warm_summary["average_execution_time_ms"]
    return {
        "cold_cache_accuracy": cold_summary["overall_accuracy"],
        "warm_cache_accuracy": warm_summary["overall_accuracy"],
        "cold_cache_average_latency_ms": cold_latency,
        "warm_cache_average_latency_ms": warm_latency,
        "cold_cache_hit_rate": cold_summary["cache_hit_rate"],
        "warm_cache_hit_rate": warm_summary["cache_hit_rate"],
        "cold_cache_miss_rate": cold_summary["cache_miss_rate"],
        "warm_cache_miss_rate": warm_summary["cache_miss_rate"],
        "latency_improvement_percent": _round_stat(((cold_latency - warm_latency) / cold_latency) * 100 if cold_latency else 0),
        "cache_hit_rate_improvement": _round_stat(warm_summary["cache_hit_rate"] - cold_summary["cache_hit_rate"]),
        "cache_miss_rate_reduction": _round_stat(cold_summary["cache_miss_rate"] - warm_summary["cache_miss_rate"]),
        "average_cache_hit_latency_ms": _round_stat(statistics.mean(hit_latencies) if hit_latencies else 0),
        "average_cache_miss_latency_ms": _round_stat(statistics.mean(miss_latencies) if miss_latencies else 0),
        "semantic_cache_effectiveness": _round_stat(warm_summary["cache_hit_rate"] - cold_summary["cache_hit_rate"]),
    }


def _build_experiment_manifest(
    experiment_name: str,
    manifest: dict[str, Any],
    settings: dict[str, Any],
    timestamp: str,
    backend_url: str,
    total_queries: int,
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "experiment_name": experiment_name,
        "benchmark_version": manifest["benchmark_version"],
        "database_name": manifest.get("database_name"),
        "database_path": manifest.get("database_path"),
        "database_engine": manifest.get("database_engine"),
        "backend_url": backend_url,
        "cache_enabled": True,
        "semantic_threshold": settings.get("similarity_threshold"),
        "llm_model": settings.get("active_llm_model"),
        "embedding_model": settings.get("embedding_model"),
        "backend_version": settings.get("semantic_sql_version"),
        "execution_timestamp": timestamp,
        "total_queries": total_queries,
        "successful_queries": summary["successful_queries"],
        "failed_queries": summary["failed_queries"],
        "python_version": _safe_metadata("python_version", platform.python_version),
        "platform": _safe_metadata("platform", platform.platform),
        "processor": _safe_metadata("processor", platform.processor),
        "git_commit_hash": _git_commit_hash(),
    }


def _write_result_files(
    results_dir: Path,
    benchmark_version: str,
    experiment_name: str,
    timestamp: str,
    all_results: list[dict[str, Any]],
    cold_results: list[dict[str, Any]],
    warm_results: list[dict[str, Any]],
    summary: dict[str, Any],
    metrics: dict[str, Any],
    cache_comparison: dict[str, Any],
    experiment_manifest: dict[str, Any],
) -> None:
    charts_dir = results_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    _write_json(results_dir / "evaluation_results.json", _result_payload(benchmark_version, experiment_name, timestamp, all_results))
    _write_json(results_dir / "cold_cache_results.json", _result_payload(benchmark_version, experiment_name, timestamp, cold_results))
    _write_json(results_dir / "warm_cache_results.json", _result_payload(benchmark_version, experiment_name, timestamp, warm_results))
    _write_json(results_dir / "evaluation_summary.json", summary)
    _write_json(results_dir / "evaluation_metrics.json", metrics)
    _write_json(results_dir / "cache_comparison.json", cache_comparison)
    _write_json(results_dir / "experiment_manifest.json", experiment_manifest)
    _write_chart_files(charts_dir, all_results, cache_comparison)


def _write_chart_files(charts_dir: Path, results: list[dict[str, Any]], cache_comparison: dict[str, Any]) -> None:
    _write_json(charts_dir / "accuracy_by_category.json", _accuracy_by_field(results, "category"))
    _write_json(charts_dir / "accuracy_by_difficulty.json", _accuracy_by_field(results, "difficulty"))
    _write_json(charts_dir / "dataset_breakdown.json", _accuracy_by_field(results, "dataset"))
    _write_json(charts_dir / "cache_statistics.json", _cache_statistics(results))
    _write_json(charts_dir / "latency_distribution.json", _latency_distribution(results))
    _write_json(charts_dir / "cold_vs_warm_cache.json", cache_comparison)
    _write_json(
        charts_dir / "generation_mode_distribution.json",
        dict(sorted(Counter(str(result.get("generation_mode") or "unknown") for result in results).items())),
    )


def _result_payload(
    benchmark_version: str,
    experiment_name: str,
    timestamp: str,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "benchmark_version": benchmark_version,
        "experiment_name": experiment_name,
        "execution_timestamp": timestamp,
        "summary": _build_summary(results),
        "results": results,
    }


def _accuracy_by_field(results: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        value = result.get(field)
        if value is not None:
            buckets[str(value)].append(result)
    return {
        key: {
            "total": len(bucket),
            "passed": sum(1 for result in bucket if result["passed"]),
            "accuracy": _percent(sum(1 for result in bucket if result["passed"]), len(bucket)),
        }
        for key, bucket in sorted(buckets.items())
    }


def _dataset_accuracy(results: list[dict[str, Any]], dataset: str) -> float:
    bucket = [result for result in results if result["dataset"] == dataset]
    return _percent(sum(1 for result in bucket if result["passed"]), len(bucket))


def _cache_statistics(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    hits = sum(1 for result in results if result["cache_hit"])
    return {
        "cache_hits": hits,
        "cache_misses": total - hits,
        "cache_hit_rate": _percent(hits, total),
        "cache_miss_rate": _percent(total - hits, total),
    }


def _latency_distribution(results: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [float(result["execution_time_ms"]) for result in results]
    return {
        "count": len(latencies),
        "average": _round_stat(statistics.mean(latencies) if latencies else 0),
        "median": _round_stat(statistics.median(latencies) if latencies else 0),
        "minimum": _round_stat(min(latencies) if latencies else 0),
        "maximum": _round_stat(max(latencies) if latencies else 0),
        "p95": _round_stat(_percentile(latencies, 95)),
        "standard_deviation": _round_stat(statistics.pstdev(latencies) if len(latencies) > 1 else 0),
    }


def _valid_failure_reason(http_status: int, validation_status: str, result_equivalent: bool, backend_error: str | None) -> str:
    if backend_error:
        return "Backend request failed."
    if http_status >= 400:
        return f"Backend returned HTTP {http_status}."
    if validation_status.lower() != "valid":
        return "Backend SQL validation failed."
    if not result_equivalent:
        return "Backend result set differs from expected SQL result."
    return "Unknown failure."


def _print_progress(name: str, current: int, total: int, start_time: float, dataset: str) -> None:
    elapsed = time.perf_counter() - start_time
    average = elapsed / current if current else 0
    remaining = max(0, total - current)
    eta = remaining * average
    print(
        f"\r{name.replace('_', ' ').title()} {current} / {total} | "
        f"remaining {remaining} | eta {_format_seconds(eta)} | dataset {dataset}",
        end="",
        flush=True,
    )


def _format_seconds(seconds: float) -> str:
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {sec}s"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


def _percent(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 3) if denominator else 0.0


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = math.ceil((percentile / 100) * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def _round_stat(value: float) -> float:
    return round(float(value), 3)


def _payload_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    return str(value) if value is not None else ""


def _payload_optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return str(value) if value is not None else None


def _payload_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key, [])
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _payload_float(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _payload_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _git_commit_hash() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return result.stdout.strip() or None


def _safe_metadata(_label: str, supplier: Any) -> str:
    try:
        value = supplier()
    except Exception:
        return "unknown"
    return str(value) if value else "unknown"


def _configure_logging(results_dir: Path) -> logging.Logger:
    logs_dir = results_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("semanticsql_benchmark")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(logs_dir / "evaluation.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


def _close_logger(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        handler.flush()
        handler.close()
        logger.removeHandler(handler)


def _load_datasets(benchmark_dir: Path) -> list[dict[str, Any]]:
    datasets: list[dict[str, Any]] = []
    for dataset_name in ("functional", "semantic", "invalid"):
        payload = _read_json(benchmark_dir / "datasets" / f"{dataset_name}.json")
        datasets.extend(payload["queries"])
    return datasets


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as input_file:
        return json.load(input_file)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=2, sort_keys=True)
        output_file.write("\n")


if __name__ == "__main__":
    main()
