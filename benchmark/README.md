# SemanticSQL Benchmark

The benchmark framework is a standalone research component for SemanticSQL. It generates deterministic natural-language-to-SQL datasets from the active database schema, validates every generated query before saving, and emits versioned manifests for reproducible experiments.

## Generate

```bash
backend/.venv/bin/python -m benchmark.generator
```

Outputs:

- `benchmark/manifest.json`
- `benchmark/statistics.json`
- `benchmark/schema_coverage.json`
- `benchmark/benchmark_quality.json`
- `benchmark/datasets/functional.json`
- `benchmark/datasets/semantic.json`
- `benchmark/datasets/invalid.json`

The generator is deterministic. Running it repeatedly against the same schema produces identical benchmark datasets except for manifest timestamps.

## Research Quality

The generator performs schema coverage analysis before saving artifacts. It tracks table, column, primary-key, foreign-key, numeric-column, text-column, join-path, and relationship-chain coverage in `schema_coverage.json`.

The valid workload is balanced by design:

- Easy: 35%
- Medium: 40%
- Hard: 25%

Consistency checks validate expected SQL, semantic-to-functional references, invalid-query failure reasons, category counts, difficulty labels, duplicate natural-language requests, and duplicate SQL templates.

`benchmark_quality.json` summarizes publication readiness using schema coverage, query diversity, semantic diversity, SQL complexity, duplicate penalties, validation results, and reproducibility.

## Evaluate

The evaluator is an end-to-end research instrument. It assumes the FastAPI backend is already running and never starts or stops application services.

```bash
uvicorn app.main:app --reload
```

Then run the evaluator from the repository root:

```bash
backend/.venv/bin/python -m benchmark.evaluate --backend-url http://127.0.0.1:8000
```

Outputs:

- `results/experiment_manifest.json`
- `results/evaluation_results.json`
- `results/evaluation_summary.json`
- `results/evaluation_metrics.json`
- `results/cold_cache_results.json`
- `results/warm_cache_results.json`
- `results/cache_comparison.json`
- `results/logs/evaluation.log`
- `results/charts/accuracy_by_category.json`
- `results/charts/accuracy_by_difficulty.json`
- `results/charts/dataset_breakdown.json`
- `results/charts/cache_statistics.json`
- `results/charts/latency_distribution.json`
- `results/charts/cold_vs_warm_cache.json`
- `results/charts/generation_mode_distribution.json`

If the backend is unreachable, the evaluator exits with a clear message and does not write partial results.

### Evaluation Workflow

For every query in `benchmark/datasets/functional.json`, `benchmark/datasets/semantic.json`, and `benchmark/datasets/invalid.json`, the evaluator sends the natural-language request to:

```text
POST /api/v1/query/process
```

It records backend SQL generation, validation, cache behavior, execution metadata, response size, and pass/fail status. Valid benchmark queries pass when the backend validates and executes successfully and the returned result set matches the expected SQL result. Invalid benchmark queries pass when the backend rejects the query or returns validation failure.

### Cold Cache Experiment

Before the first pass, the evaluator attempts to clear the semantic cache through the existing cache service. It does not create a new cache endpoint or modify the backend. The full benchmark is then executed once and stored in `results/cold_cache_results.json`.

### Warm Cache Experiment

Immediately after the cold-cache pass, the evaluator executes the identical benchmark again without clearing cache state. Results are stored in `results/warm_cache_results.json`.

### Metric Definitions

- `overall_accuracy`: percentage of all evaluated queries that passed.
- `functional_accuracy`: pass rate for the functional dataset.
- `semantic_accuracy`: pass rate for semantic paraphrase queries.
- `invalid_detection_accuracy`: pass rate for invalid benchmark queries.
- `sql_equivalence_rate`: percentage of valid queries where generated SQL normalizes to expected SQL with `sqlglot`.
- `result_equivalence_rate`: percentage of valid queries where backend results match direct expected-SQL execution.
- `cache_hit_rate` / `cache_miss_rate`: percentage of responses reported as semantic cache hits or misses.
- `average_execution_time_ms`, `median_execution_time_ms`, `p95_execution_time_ms`: latency metrics using backend execution time when exposed, otherwise evaluator wall-clock timing.
- `validation_failure_rate`: percentage of responses whose validation status is not `valid`.
- `average_similarity_score`: mean semantic cache similarity reported by the backend.
- `generation_mode_distribution`: count of `Rule`, `LLM`, or other backend-reported generation modes.
- `latency_improvement_percent`: cold-to-warm average latency reduction.
- `semantic_cache_effectiveness`: warm cache hit-rate increase over cold cache hit rate.

### Result Correctness

Expected SQL is executed directly against the benchmark SQLite database only when it is a `SELECT` statement. Non-`SELECT` expected SQL is skipped and recorded as a warning. Result comparison ignores row ordering unless the expected SQL contains `ORDER BY`, normalizes `NULL`, rounds floating-point values, normalizes integer types, and compares complete row contents.

### Reproducibility Metadata

`results/experiment_manifest.json` stores the benchmark version, database metadata, backend URL, semantic threshold, active LLM model, embedding model, Python version, platform, backend version when exposed by settings, and git commit hash when available.

## Versioning

The benchmark version lives in `benchmark/manifest.json` and is copied into every generated dataset and evaluation result file.

## Database Adapters

Database-specific logic is isolated under `benchmark/adapters/`. The current implementation uses `SQLiteAdapter`; future PostgreSQL, MySQL, MariaDB, and SQL Server adapters can implement the same `DatabaseAdapter` protocol without changing the generator or evaluator architecture.
