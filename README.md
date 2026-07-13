# SemanticSQL

> **A Hybrid Rule-Based and LLM-Assisted Framework for Natural Language-to-SQL Generation with Semantic Caching**

SemanticSQL is an AI-powered Natural Language-to-SQL (NL2SQL) framework that enables users to query relational databases using natural language instead of writing SQL manually. The framework combines deterministic rule-based query generation, Large Language Model (LLM)-assisted SQL synthesis, semantic caching, and schema-aware validation to improve query accuracy, execution efficiency, and response latency.

Developed as part of the **M.Tech (Computer Science & Engineering)** program at **R. V. College of Engineering, Bengaluru**.

---

## Features

- Natural Language → SQL conversion
- Hybrid rule-based and LLM-assisted SQL generation
- Semantic caching using Redis and Sentence Transformers
- Schema-aware SQL validation
- Runtime model selection using Ollama
- Configurable semantic similarity threshold
- FastAPI backend
- React + TypeScript + Material UI frontend
- SQLite (default) and MySQL support
- Automated benchmark generation
- Comprehensive benchmark evaluation
- Query analytics and cache monitoring
- Modular and extensible architecture

---

# Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | React, TypeScript, Material UI |
| Backend | FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite / MySQL |
| LLM | Ollama (Llama 3.1) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Cache | Redis |
| SQL Validation | SQLGlot |

---

# Repository Structure

```text
SemanticSQL
│
├── backend/          FastAPI backend
├── frontend/         React frontend
├── benchmark/        Benchmark generation and evaluation
├── docs/             Documentation
├── design/           Design documents
├── paper/            IEEE paper and figures
├── results/          Benchmark outputs
├── README.md
├── LICENSE
└── .gitignore
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/dhruvak99/semanticSQL.git

cd semanticSQL
```

---

## Backend Setup

> Recommended Python version: **Python 3.11 or newer**.

```bash
cd backend

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

---

## Frontend Setup

```bash
cd ../frontend

npm install
```

---

## Install and Start Redis

SemanticSQL uses Redis for semantic caching.

Start the Redis server:

```bash
redis-server
```

Verify Redis is running:

```bash
redis-cli ping
```

Expected output:

```text
PONG
```

> **Note:** If Redis is unavailable, SemanticSQL automatically falls back to an in-memory semantic cache.

---

## Install Ollama

Download and install Ollama from:

https://ollama.com/download

Pull the default language model used by SemanticSQL:

```bash
ollama pull llama3.1:8b
```

Verify the installed models:

```bash
ollama list
```

Start the Ollama server (if it is not already running):

```bash
ollama serve
```

> **Note:** On macOS and Windows, Ollama usually starts automatically after installation. Running `ollama serve` is only required if the service is not already running.

---

## Start the Backend

```bash
cd backend

source .venv/bin/activate

uvicorn app.main:app --reload
```

---

## Start the Frontend

Open a new terminal:

```bash
cd frontend

npm run dev
```
---

# Database Configuration

No database server is required.

If `DATABASE_URL` is not configured, SemanticSQL automatically creates and uses

```text
backend/semanticsql.db
```

during startup.

Sample employee data is automatically inserted if the database is empty.

To use MySQL instead, create

```text
backend/.env
```

and configure

```text
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/semanticsql
```

---

# Semantic Cache

SemanticSQL uses

- sentence-transformers
- all-MiniLM-L6-v2

to generate embeddings for incoming natural language queries.

Each cache entry stores

- Natural language query
- Query embedding
- Generated SQL
- Query result
- Timestamp
- Hit count

Redis is used whenever available.

If Redis is unavailable, SemanticSQL automatically falls back to an in-memory cache.

Optional configuration

```text
REDIS_URL=redis://localhost:6379/0

SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.90

SEMANTIC_CACHE_MODEL_NAME=all-MiniLM-L6-v2
```

---

# Running the Benchmark

SemanticSQL includes an automated benchmark framework capable of generating, validating, and evaluating Natural Language-to-SQL datasets.

## Step 1 — Generate Benchmark Dataset

```bash
cd benchmark

python generator.py
```

This creates benchmark datasets covering

- Functional queries
- Semantic paraphrases
- Invalid queries

---

## Step 2 — Validate the Benchmark

```bash
python validation.py
```

Validation verifies

- SQL syntax
- Schema consistency
- Query correctness
- Dataset quality

---

## Step 3 — Start Backend

```bash
cd ../backend

source .venv/bin/activate

uvicorn app.main:app --reload
```

---

## Step 4 — Run Benchmark Evaluation


> **Prerequisites**
>
> Before running the benchmark, ensure that:
>
> - Redis server is running (`redis-server`)
> - Ollama is installed and running (`ollama serve`, if required)
> - The default model has been downloaded (`ollama pull llama3.1:8b`)
> - The FastAPI backend is running

Open a new terminal

```bash
cd benchmark

python evaluate.py
```

The evaluation automatically measures

- Overall Accuracy
- Functional Accuracy
- Semantic Accuracy
- Invalid Query Detection
- Result Equivalence
- SQL Equivalence
- Cache Hit Rate
- Cache Miss Rate
- Query Latency
- Failure Analysis
- Difficulty-wise Performance

Benchmark reports are written to the repository's results and benchmark output files.

---

# Regenerating Paper Figures

The figures presented in the IEEE paper can be regenerated using

```bash
cd paper/figures

python generate_figure3.py

python generate_figure4.py

python generate_figure5.py

python generate_figure6.py
```

These scripts generate

- SQL Category Accuracy
- Semantic Cache Performance
- Failure Pareto Analysis
- Query Difficulty Analysis

---

# Experimental Results

| Metric | Value |
|--------|-------:|
| Overall Accuracy | **46.47%** |
| Functional Accuracy | **48.17%** |
| Semantic Accuracy | **47.13%** |
| Invalid Query Detection | **31.50%** |
| Result Equivalence | **54.06%** |
| SQL Equivalence | **1.72%** |
| Average Execution Time | **295.74 ms** |

---

# Architecture

The SemanticSQL pipeline consists of

```
Natural Language Query
        │
        ▼
 Preprocessing
        │
        ▼
 Semantic Embedding
        │
        ▼
 Semantic Cache
    │          │
 Cache Hit   Cache Miss
    │          │
    ▼          ▼
 Cached SQL   LLM SQL Generation
                  │
                  ▼
         Schema Validation
                  │
                  ▼
            SQL Execution
                  │
                  ▼
             Cache Update
                  │
                  ▼
             Query Results
```

---

# Future Work

Future improvements include

- Adaptive semantic cache thresholds
- AI-driven rule generation
- Improved clause-specific SQL generation
- Value grounding and entity resolution
- Multi-turn conversational querying
- Multi-database support
- Distributed semantic caching
- Benchmarking on Spider, BIRD, and WikiSQL

---

# Paper

**SemanticSQL: A Hybrid Rule-Based and LLM-Assisted Framework for Natural Language-to-SQL Generation with Semantic Caching**

The accompanying IEEE conference paper and supporting figures are available in the `paper/` directory.

---

# License

This project is released under the MIT License.

See the `LICENSE` file for details.

---

# Authors

**Dr. Shanta Rangaswamy**  
Head of Department  
Department of Computer Science and Engineering  
R. V. College of Engineering

**Dr. Hemavathy R.**  
Department of Computer Science and Engineering  
R. V. College of Engineering

**Rohith Arsha**  
M.Tech Computer Science and Engineering  
R. V. College of Engineering

**Dhruva K**  
M.Tech Computer Science and Engineering  
R. V. College of Engineering

---

# Citation

If you use this project in your research, please cite:

```bibtex
@software{SemanticSQL2026,
  title={SemanticSQL: A Hybrid Rule-Based and LLM-Assisted Framework for Natural Language-to-SQL Generation with Semantic Caching},
  author={Dhruva K and Rohith Arsha and Hemavathy R.},
  year={2026},
  url={https://github.com/dhruvak99/semanticSQL}
}
```