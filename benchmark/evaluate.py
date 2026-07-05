from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.adapters import SQLiteAdapter
from benchmark.validation import validate_sql_against_schema


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a generated SemanticSQL benchmark.")
    parser.add_argument("--benchmark-dir", default="benchmark", help="Directory containing manifest.json.")
    parser.add_argument("--results-dir", default="results", help="Directory where experiment outputs are written.")
    parser.add_argument("--experiment-name", default="SemanticSQL Benchmark Evaluation")
    parser.add_argument("--cache-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--semantic-threshold", type=float, default=0.90)
    parser.add_argument("--llm-model", default="llama3.1:8b")
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2")
    args = parser.parse_args()

    benchmark_dir = Path(args.benchmark_dir)
    results_dir = Path(args.results_dir)
    manifest = _read_json(benchmark_dir / "manifest.json")
    adapter = SQLiteAdapter(database_path=manifest["database_path"])
    schema = adapter.introspect()
    datasets = _load_datasets(benchmark_dir)

    evaluations = []
    successful_queries = 0
    failed_queries = 0
    for query in datasets:
        validation = validate_sql_against_schema(query["expected_sql"], schema)
        expected_valid = query["dataset"] != "invalid"
        passed = validation.valid == expected_valid
        successful_queries += int(passed)
        failed_queries += int(not passed)
        evaluations.append(
            {
                "benchmark_version": manifest["benchmark_version"],
                "query_id": query["id"],
                "dataset": query["dataset"],
                "expected_valid": expected_valid,
                "validation_valid": validation.valid,
                "validation_errors": list(validation.errors),
                "passed": passed,
            }
        )

    timestamp = datetime.now(UTC).isoformat()
    experiment_manifest = {
        "experiment_name": args.experiment_name,
        "benchmark_version": manifest["benchmark_version"],
        "database_name": manifest["database_name"],
        "cache_enabled": args.cache_enabled,
        "semantic_threshold": args.semantic_threshold,
        "llm_model": args.llm_model,
        "embedding_model": args.embedding_model,
        "execution_timestamp": timestamp,
        "total_queries": len(datasets),
        "successful_queries": successful_queries,
        "failed_queries": failed_queries,
        "result_file": "results/evaluation_results.json",
    }

    results_dir.mkdir(parents=True, exist_ok=True)
    _write_json(results_dir / "experiment_manifest.json", experiment_manifest)
    _write_json(
        results_dir / "evaluation_results.json",
        {
            "benchmark_version": manifest["benchmark_version"],
            "experiment_name": args.experiment_name,
            "execution_timestamp": timestamp,
            "summary": {
                "total_queries": len(datasets),
                "successful_queries": successful_queries,
                "failed_queries": failed_queries,
            },
            "results": evaluations,
        },
    )


def _load_datasets(benchmark_dir: Path) -> list[dict[str, Any]]:
    datasets: list[dict[str, Any]] = []
    for dataset_name in ("functional", "semantic", "invalid"):
        payload = _read_json(benchmark_dir / "datasets" / f"{dataset_name}.json")
        datasets.extend(payload["queries"])
    return datasets


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

