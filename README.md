# SemanticSQL

AI-powered natural language interface for relational databases.

## Apps

- `frontend`: React, TypeScript, Material UI, route-driven application shell.
- `backend`: FastAPI, SQLAlchemy, Redis, versioned API package structure.

## Development

```bash
cd frontend
npm install
npm run dev
```

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Use Python 3.11 through 3.14. If an older virtualenv fails while importing SQLAlchemy, reinstall dependencies with `pip install -r requirements.txt`; the project pins SQLAlchemy to a Python 3.14-compatible release.

## Backend Database Configuration

For local development, no database server is required. If `DATABASE_URL` is not set, the backend automatically creates and uses:

```bash
backend/semanticsql.db
```

On startup, SemanticSQL creates the `employees` table if it does not exist and seeds sample employee data if the table is empty.

To use MySQL later, create `backend/.env` and set `DATABASE_URL`:

```bash
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/semanticsql
```

The query execution layer is read-only. It only executes `SELECT` statements, including `DISTINCT`, `COUNT`, and `GROUP BY` queries. Mutating or destructive statements such as `DROP`, `TRUNCATE`, `DELETE`, `UPDATE`, `ALTER`, `INSERT`, and `CREATE` are blocked by the API execution layer.

## Optional MySQL Sample Schema

SQLite setup is automatic. If you switch to MySQL, run these SQL commands to create the required schema and sample employee data:

```sql
CREATE DATABASE IF NOT EXISTS semanticsql;
USE semanticsql;

CREATE TABLE IF NOT EXISTS employees (
  employee_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  department VARCHAR(100) NOT NULL,
  salary DECIMAL(12, 2) NOT NULL,
  joining_date DATE NOT NULL
);

TRUNCATE TABLE employees;

INSERT INTO employees (employee_id, name, email, department, salary, joining_date) VALUES
  (101, 'David Wilson', 'david.wilson@company.com', 'Engineering', 75000.00, '2019-07-18'),
  (104, 'Sarah Johnson', 'sarah.johnson@company.com', 'Finance', 88000.00, '2020-03-22'),
  (107, 'Michael Brown', 'michael.brown@company.com', 'Finance', 95000.00, '2021-05-10'),
  (109, 'Jessica Lee', 'jessica.lee@company.com', 'Finance', 72000.00, '2022-01-15'),
  (115, 'Daniel Martinez', 'daniel.martinez@company.com', 'Operations', 68000.00, '2021-11-30'),
  (121, 'Priya Raman', 'priya.raman@company.com', 'Human Resources', 54000.00, '2023-02-06'),
  (126, 'Ava Thompson', 'ava.thompson@company.com', 'Engineering', 99000.00, '2020-09-14'),
  (131, 'Noah Garcia', 'noah.garcia@company.com', 'Operations', 48000.00, '2022-04-03');
```
