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

```bash
backend/.venv/bin/python -m benchmark.evaluate
```

Outputs:

- `results/experiment_manifest.json`
- `results/evaluation_results.json`

## Versioning

The benchmark version lives in `benchmark/manifest.json` and is copied into every generated dataset and evaluation result file.

## Database Adapters

Database-specific logic is isolated under `benchmark/adapters/`. The current implementation uses `SQLiteAdapter`; future PostgreSQL, MySQL, MariaDB, and SQL Server adapters can implement the same `DatabaseAdapter` protocol without changing the generator or evaluator architecture.
