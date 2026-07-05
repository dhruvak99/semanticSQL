# SemanticSQL Benchmark Failure Analysis

Generated: 2026-07-05T16:09:54.765716+00:00

## Executive Summary

The completed evaluation contains **3800** query executions across cold and warm cache passes. **1134** passed and **2666** failed, for an overall accuracy of **29.842%**.

The dominant failure mode is not SQL syntax. Most failures are valid SQL that returns a result set different from the benchmark expected SQL. A particularly important finding is that aggregate categories (`AVG`, `COUNT`, `MIN`, `MAX`, `SUM`) report **0% accuracy** largely because expected aggregate aliases such as `avg_price` or `row_count` are compared as result-column names against backend-generated scalar aggregate outputs such as `AVG(price)` or `COUNT(*)`. Many of those queries compute the same scalar value but fail strict row-dictionary comparison because column keys differ.

## Failure Breakdown

### By Root Cause
|Root Cause|Failures|
|---|---|
|Aggregate result alias mismatch in evaluator comparison|717|
|Wrong or invented column|455|
|GROUP BY result mismatch|204|
|Wrong aggregate function|145|
|LIMIT clause mismatch|140|
|WHERE clause error|134|
|ORDER BY mismatch|103|
|Aggregate result mismatch|94|
|DISTINCT/projection mismatch|88|
|JOIN result mismatch|82|
|Invalid query accepted via cached valid SQL|74|
|SQL syntax error|67|
|EXISTS clause mismatch|56|
|Nested query result mismatch|55|
|Missing aggregate function|47|
|IN clause mismatch|45|
|HAVING clause mismatch|31|
|Invalid query repaired into valid SQL|26|
|Backend exception / HTTP failure|23|
|Invented non-schema column: stored|20|
|Wrong or invented table|19|
|Projection mismatch|17|
|Backend rejected generated SQL request|12|
|Result-set mismatch|8|
|Validation failure|4|

### By SQL Category
|Category|Failures|
|---|---|
|COUNT|300|
|AVG|240|
|GROUP_BY|217|
|JOIN|206|
|MIN|180|
|MAX|180|
|SUM|180|
|NESTED|171|
|LIMIT|170|
|WHERE|164|
|ORDER_BY|129|
|DISTINCT|103|
|HAVING|100|
|None|100|
|EXISTS|91|
|IN|69|
|SELECT|66|

### By Dataset
|Dataset|Failures|
|---|---|
|semantic|2159|
|functional|407|
|invalid|100|

### By Difficulty
|Difficulty|Failures|
|---|---|
|medium|1080|
|easy|932|
|hard|554|
|None|100|

### By Generation Mode
|Generation Mode|Failures|
|---|---|
|LLM|2623|
|None|35|
|Rule|8|

## Aggregate Category Analysis

Aggregate totals across cold and warm runs:

|Category|Total|Passed|Failed|Accuracy %|Root Causes|
|---|---|---|---|---|---|
|AVG|240|0|240|0.0|{'Aggregate result alias mismatch in evaluator comparison': 186, 'Aggregate result mismatch': 33, 'Wrong or invented column': 10, 'Wrong aggregate function': 8, 'Missing aggregate function': 2, 'Backend rejected generated SQL request': 1}|
|COUNT|300|0|300|0.0|{'Aggregate result alias mismatch in evaluator comparison': 211, 'Aggregate result mismatch': 40, 'Missing aggregate function': 37, 'SQL syntax error': 4, 'Wrong or invented column': 4, 'Wrong aggregate function': 3, 'Backend rejected generated SQL request': 1}|
|MIN|180|0|180|0.0|{'Aggregate result alias mismatch in evaluator comparison': 132, 'Wrong or invented column': 17, 'Aggregate result mismatch': 16, 'Wrong aggregate function': 13, 'Backend exception / HTTP failure': 1, 'Missing aggregate function': 1}|
|MAX|180|0|180|0.0|{'Aggregate result alias mismatch in evaluator comparison': 101, 'Wrong aggregate function': 48, 'Wrong or invented column': 22, 'Missing aggregate function': 5, 'Aggregate result mismatch': 3, 'Backend exception / HTTP failure': 1}|
|SUM|180|0|180|0.0|{'Aggregate result alias mismatch in evaluator comparison': 87, 'Wrong aggregate function': 73, 'Wrong or invented column': 12, 'Backend rejected generated SQL request': 4, 'Aggregate result mismatch': 2, 'Missing aggregate function': 2}|

Evidence indicates mixed causes:

- **Evaluator/result-comparison issue:** many aggregate expected SQL statements include aliases (`AS avg_price`, `AS row_count`) while generated SQL omits aliases. The scalar value can match, but row dictionaries differ by key.
- **LLM generation issue:** some aggregate requests produce the wrong aggregate function, especially `MIN`, `MAX`, or `SUM` turning into `AVG`.
- **Validation/schema issue:** a smaller subset is invalid because generated SQL references non-schema columns or malformed constructs.
- **Backend/runtime issue:** a small number of aggregate queries return HTTP errors.

This pattern does not indicate a benchmark issue from the available evidence; expected SQL executes read-only against the benchmark database. It also does not primarily indicate validation failure, because most aggregate failures have `validation_status = valid`.

## Top 20 Recurring Failure Patterns

|Pattern|Failures|
|---|---|
|Generated SQL referenced unavailable column|455|
|COUNT: scalar aggregate value matches but output alias differs|211|
|GROUP BY result mismatch|204|
|AVG: scalar aggregate value matches but output alias differs|186|
|LIMIT clause mismatch|140|
|WHERE predicate semantics changed (operator/value/projection drift)|134|
|MIN: scalar aggregate value matches but output alias differs|132|
|ORDER BY mismatch|103|
|MAX: scalar aggregate value matches but output alias differs|101|
|Aggregate result mismatch|94|
|DISTINCT/projection mismatch|88|
|SUM: scalar aggregate value matches but output alias differs|87|
|JOIN result mismatch|82|
|Invalid request hit semantic cache entry containing valid SQL|74|
|SQL syntax error|67|
|EXISTS clause mismatch|56|
|Nested query result mismatch|55|
|Missing aggregate function|47|
|IN clause mismatch|45|
|MAX: expected ['MAX'] but generated ['MIN']|41|

## Success Analysis

Successful queries generally succeed when generated SQL either exactly matches the expected SQL or returns an equivalent result set. Success is strongest for direct `SELECT`, `IN`, `HAVING`, and `EXISTS`-style patterns, and weakest for aggregates and limit/order/projection-sensitive requests.

|Successful Pattern|Count|
|---|---|
|LLM path success|1131|
|Different SQL but equivalent result set|1066|
|Cache hit preserved correctness|922|
|Exact SQL equivalence|68|

## Cache Analysis

Cold cache accuracy: **29.737%**. Warm cache accuracy: **29.947%**. The warm cache hit rate increased from **54.368%** to **99.263%**, and average latency improved from **308.967 ms** to **112.77 ms**.

Correctness barely changed between cold and warm passes. This indicates the semantic cache primarily improves latency and reuses prior behavior. It does not repair incorrect SQL. In some invalid-query failures, cache hits propagated valid SQL for invalid requests, so cache can preserve wrong accept/reject behavior once stored.

## Ranked Root Causes

|Rank|Root Cause|Failures|Failure Share %|Potential Accuracy Gain|
|---|---|---|---|---|
|1|Aggregate/evaluator result comparison issue|717|26.89|18.87|
|2|Clause-specific SQL generation drift|478|17.93|12.58|
|3|Schema grounding / invented column issue|475|17.82|12.5|
|4|Aggregate SQL generation/result issue|286|10.73|7.53|
|5|Predicate/projection semantic drift|239|8.96|6.29|
|6|Join/subquery SQL generation drift|238|8.93|6.26|
|7|Invalid-query rejection weakness|100|3.75|2.63|
|8|SQL syntax error|67|2.51|1.76|
|9|Backend/runtime stability issue|23|0.86|0.61|
|10|Schema grounding / invented table issue|19|0.71|0.5|
|11|Backend/runtime validation rejection|12|0.45|0.32|
|12|Result-set mismatch|8|0.3|0.21|
|13|Validation failure|4|0.15|0.11|

## Recommendations (Analysis Only)

|Rank|Recommendation|Reason|
|---|---|---|
|1|Fix aggregate result comparison or align aggregate aliases|Highest immediate impact because AVG/COUNT/MIN/MAX/SUM are all 0%, and many examples have identical scalar values with different aliases.|
|2|Strengthen invalid-query rejection before SQL generation/cache lookup|Invalid benchmark queries are often transformed into valid SQL and 50% are not rejected.|
|3|Improve NL-to-SQL projection and predicate preservation|Many valid SQL outputs use SELECT * or change >= to >/<, causing result mismatch despite valid SQL.|
|4|Tighten schema grounding against invented stored/available columns|Stored/available phrasing leads to non-schema column `stored` and validation failures.|
|5|Improve clause-specific prompting for LIMIT, ORDER BY, GROUP BY, JOIN, IN, EXISTS|These categories fail through clause omission or semantic drift rather than syntax alone.|

## Representative Failure Examples

### Aggregate result alias mismatch in evaluator comparison
- **F0081 (cold_cache, functional, COUNT)**
  - NL: `Count authors records where author id is at least 0.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM authors WHERE author_id >= 0;`
  - Generated SQL: `SELECT COUNT(*) FROM authors WHERE author_id >= 0`
  - Executed SQL: `SELECT COUNT(*) FROM authors WHERE author_id >= 0`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 4}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 4}]
  - Failure: Backend result set differs from expected SQL result.
- **F0082 (cold_cache, functional, COUNT)**
  - NL: `How many books have title has at least 2 characters?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 2;`
  - Generated SQL: `SELECT COUNT(*) FROM books WHERE LENGTH(title) >= 2`
  - Executed SQL: `SELECT COUNT(*) FROM books WHERE LENGTH(title) >= 2`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 5}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 5}]
  - Failure: Backend result set differs from expected SQL result.
- **F0083 (cold_cache, functional, COUNT)**
  - NL: `Return the number of departments after filtering for location has at least 3 characters.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM departments WHERE location IS NOT NULL AND LENGTH(location) >= 3;`
  - Generated SQL: `SELECT COUNT(*)
FROM departments
WHERE LENGTH(location) >= 3`
  - Executed SQL: `SELECT COUNT(*)
FROM departments
WHERE LENGTH(location) >= 3`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 5}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 5}]
  - Failure: Backend result set differs from expected SQL result.
- **F0084 (cold_cache, functional, COUNT)**
  - NL: `Count employee projects records where hours per week is at least 3.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM employee_projects WHERE hours_per_week >= 3;`
  - Generated SQL: `SELECT COUNT(*) FROM employee_projects WHERE hours_per_week >= 3`
  - Executed SQL: `SELECT COUNT(*) FROM employee_projects WHERE hours_per_week >= 3`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0085 (cold_cache, functional, COUNT)**
  - NL: `How many employees have salary is at least 4?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM employees WHERE salary >= 4;`
  - Generated SQL: `SELECT COUNT(*) FROM employees WHERE CAST(salary AS DECIMAL(12,2)) >= 4`
  - Executed SQL: `SELECT COUNT(*) FROM employees WHERE CAST(salary AS DECIMAL(12,2)) >= 4`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 8}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 8}]
  - Failure: Backend result set differs from expected SQL result.
- **F0086 (cold_cache, functional, COUNT)**
  - NL: `Return the number of products after filtering for price is at least 5.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM products WHERE price >= 5;`
  - Generated SQL: `SELECT COUNT(product_id) FROM products WHERE price >= 5`
  - Executed SQL: `SELECT COUNT(product_id) FROM products WHERE price >= 5`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 2}]
  - Actual Result: rows=1 columns=['COUNT(product_id)'] sample=[{'COUNT(product_id)': 2}]
  - Failure: Backend result set differs from expected SQL result.
- **F0087 (cold_cache, functional, COUNT)**
  - NL: `Count projects records where project id is at least 6.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM projects WHERE project_id >= 6;`
  - Generated SQL: `SELECT COUNT(*) FROM projects WHERE project_id >= 6`
  - Executed SQL: `SELECT COUNT(*) FROM projects WHERE project_id >= 6`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0088 (cold_cache, functional, COUNT)**
  - NL: `How many query history have rows returned is at least 7?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM query_history WHERE rows_returned >= 7;`
  - Generated SQL: `SELECT COUNT(*) FROM query_history WHERE rows_returned >= 7`
  - Executed SQL: `SELECT COUNT(*) FROM query_history WHERE rows_returned >= 7`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 183}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 183}]
  - Failure: Backend result set differs from expected SQL result.
- **F0089 (cold_cache, functional, COUNT)**
  - NL: `Return the number of vendors after filtering for id is at least 8.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM vendors WHERE id >= 8;`
  - Generated SQL: `SELECT COUNT(*) FROM vendors WHERE id >= 8`
  - Executed SQL: `SELECT COUNT(*) FROM vendors WHERE id >= 8`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0091 (cold_cache, functional, COUNT)**
  - NL: `How many books have author id is at least 10?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM books WHERE author_id >= 10;`
  - Generated SQL: `SELECT COUNT(*) FROM books WHERE author_id >= 10`
  - Executed SQL: `SELECT COUNT(*) FROM books WHERE author_id >= 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 0}]
  - Failure: Backend result set differs from expected SQL result.
### Wrong or invented column
- **F0054 (cold_cache, functional, LIMIT)**
  - NL: `Show 6 employee projects records from this page.`
  - Expected SQL: `SELECT hours_per_week FROM employee_projects LIMIT 6 OFFSET 3;`
  - Generated SQL: `SELECT * FROM employee_projects WHERE ROWID IN ( SELECT ROWID FROM employee_projects ORDER BY RANDOM() LIMIT 6 );`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'ROWID' does not exist in table 'employee_projects'"]
  - Expected Result: rows=0 columns=['hours_per_week'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0063 (cold_cache, functional, LIMIT)**
  - NL: `Show 5 employee projects records from this page.`
  - Expected SQL: `SELECT employee_id FROM employee_projects LIMIT 5 OFFSET 0;`
  - Generated SQL: `SELECT * FROM employee_projects WHERE ROWID IN ( SELECT ROWID FROM employee_projects ORDER BY RANDOM() LIMIT 6 );`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'ROWID' does not exist in table 'employee_projects'"]
  - Expected Result: rows=0 columns=['employee_id'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0074 (cold_cache, functional, DISTINCT)**
  - NL: `Which different vendor name values exist for vendors with vendor name has at least 9 characters?`
  - Expected SQL: `SELECT DISTINCT vendor_name FROM vendors WHERE vendor_name IS NOT NULL AND LENGTH(vendor_name) >= 9 ORDER BY vendor_name ASC;`
  - Generated SQL: `SELECT DISTINCT vendor_name FROM vendors WHERE vendor_name LIKE "%_______%"`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column '%_______%' does not exist in table 'vendors'"]
  - Expected Result: rows=4 columns=['vendor_name'] sample=[{'vendor_name': 'ABC Traders'}, {'vendor_name': 'Global Supplies'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0134 (cold_cache, functional, MIN)**
  - NL: `Show the lowest rating value for vendors across all records.`
  - Expected SQL: `SELECT MIN(rating) AS min_rating FROM vendors;`
  - Generated SQL: `SELECT MIN(value) FROM vendors`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'value' does not exist in table 'vendors'"]
  - Expected Result: rows=1 columns=['min_rating'] sample=[{'min_rating': 4.0}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0149 (cold_cache, functional, MAX)**
  - NL: `Show the highest rating value for vendors across all records.`
  - Expected SQL: `SELECT MAX(rating) AS max_rating FROM vendors;`
  - Generated SQL: `SELECT MIN(value) FROM vendors`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'value' does not exist in table 'vendors'"]
  - Expected Result: rows=1 columns=['max_rating'] sample=[{'max_rating': 4.8}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0199 (cold_cache, functional, NESTED)**
  - NL: `Show employee projects whose keys appear in a subquery where hours per week is at least 3.`
  - Expected SQL: `SELECT * FROM employee_projects WHERE project_id IN (SELECT project_id FROM employee_projects WHERE hours_per_week >= 3);`
  - Generated SQL: `SELECT ep.* 
FROM employee_projects ep 
WHERE ep.employee_id IN ( SELECT ep2.employee_id FROM employee_projects ep2 WHERE ep2.hours_per_week >= 3 );`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column '*' does not exist in table 'employee_projects'"]
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0208 (cold_cache, functional, NESTED)**
  - NL: `Show employee projects whose keys appear in a subquery where hours per week is at least 12.`
  - Expected SQL: `SELECT * FROM employee_projects WHERE employee_id IN (SELECT employee_id FROM employee_projects WHERE hours_per_week >= 12);`
  - Generated SQL: `SELECT ep.* 
FROM employee_projects ep 
WHERE ep.employee_id IN ( SELECT ep2.employee_id FROM employee_projects ep2 WHERE ep2.hours_per_week >= 3 );`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column '*' does not exist in table 'employee_projects'"]
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0209 (cold_cache, functional, NESTED)**
  - NL: `Find employees selected by a nested condition with salary is at least 13.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 13);`
  - Generated SQL: `SELECT * FROM employees WHERE (salary >= 13) AND (employees.selected IS TRUE OR employees.nested = true);`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'nested' does not exist in table 'employees'", "Column 'selected' does not exist in table 'employees'"]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0217 (cold_cache, functional, NESTED)**
  - NL: `Show employee projects whose keys appear in a subquery where hours per week is at least 21.`
  - Expected SQL: `SELECT * FROM employee_projects WHERE project_id IN (SELECT project_id FROM employee_projects WHERE hours_per_week >= 21);`
  - Generated SQL: `SELECT ep.* 
FROM employee_projects ep 
WHERE ep.employee_id IN ( SELECT ep2.employee_id FROM employee_projects ep2 WHERE ep2.hours_per_week >= 3 );`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column '*' does not exist in table 'employee_projects'"]
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0218 (cold_cache, functional, NESTED)**
  - NL: `Find employees selected by a nested condition with salary is at least 22.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 22);`
  - Generated SQL: `SELECT * FROM employees WHERE ((condition) AND (salary >= 22))`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'condition' does not exist in table 'employees'"]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
### GROUP BY result mismatch
- **F0171 (cold_cache, functional, GROUP_BY)**
  - NL: `Break down authors by author name where author name has at least 1 characters.`
  - Expected SQL: `SELECT author_name, COUNT(*) AS row_count FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1 GROUP BY author_name ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT author_id FROM authors GROUP BY author_name HAVING LENGTH(author_name) > 0`
  - Executed SQL: `SELECT author_id FROM authors GROUP BY author_name HAVING LENGTH(author_name) > 0`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_name', 'row_count'] sample=[{'author_name': 'Robert Martin', 'row_count': 1}, {'author_name': 'Martin Fowler', 'row_count': 1}]
  - Actual Result: rows=4 columns=['author_id'] sample=[{'author_id': 3}, {'author_id': 4}]
  - Failure: Backend result set differs from expected SQL result.
- **F0172 (cold_cache, functional, GROUP_BY)**
  - NL: `Count books for each title after filtering for title has at least 2 characters.`
  - Expected SQL: `SELECT title, COUNT(*) AS row_count FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 2 GROUP BY title ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT COUNT(*) , title FROM books WHERE LENGTH(title) >= 2 GROUP BY title`
  - Executed SQL: `SELECT COUNT(*) , title FROM books WHERE LENGTH(title) >= 2 GROUP BY title`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['title', 'row_count'] sample=[{'title': 'Refactoring', 'row_count': 1}, {'title': 'Modern Operating Systems', 'row_count': 1}]
  - Actual Result: rows=5 columns=['COUNT(*)', 'title'] sample=[{'COUNT(*)': 1, 'title': 'Clean Architecture'}, {'COUNT(*)': 1, 'title': 'Clean Code'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0173 (cold_cache, functional, GROUP_BY)**
  - NL: `Summarize departments grouped by department name with department name has at least 3 characters.`
  - Expected SQL: `SELECT department_name, COUNT(*) AS row_count FROM departments WHERE department_name IS NOT NULL AND LENGTH(department_name) >= 3 GROUP BY department_name ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT SUM(hours_per_week) 
FROM employee_projects e 
JOIN employees em ON e.employee_id = em.employee_id 
JOIN departments d ON em.department = d.department_name 
WHERE LENGTH(d.department_name) >= 3 GROUP BY d.department_name`
  - Executed SQL: `SELECT SUM(hours_per_week) 
FROM employee_projects e 
JOIN employees em ON e.employee_id = em.employee_id 
JOIN departments d ON em.department = d.department_name 
WHERE LENGTH(d.department_name) >= 3 GROUP BY d.department_name`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3 columns=['department_name', 'row_count'] sample=[{'department_name': 'Research', 'row_count': 1}, {'department_name': 'Marketing', 'row_count': 1}]
  - Actual Result: rows=0 columns=['SUM(hours_per_week)'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0176 (cold_cache, functional, GROUP_BY)**
  - NL: `Summarize products grouped by product name with product name has at least 6 characters.`
  - Expected SQL: `SELECT product_name, COUNT(*) AS row_count FROM products WHERE product_name IS NOT NULL AND LENGTH(product_name) >= 6 GROUP BY product_name ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT SUM(price) FROM products GROUP BY product_name HAVING LENGTH(product_name) >= 6`
  - Executed SQL: `SELECT SUM(price) FROM products GROUP BY product_name HAVING LENGTH(product_name) >= 6`
  - Validation: `valid` errors=[]
  - Expected Result: rows=2 columns=['product_name', 'row_count'] sample=[{'product_name': 'Cache Booster', 'row_count': 1}, {'product_name': 'Analytics Pack', 'row_count': 1}]
  - Actual Result: rows=2 columns=['SUM(price)'] sample=[{'SUM(price)': 49.99}, {'SUM(price)': 19.99}]
  - Failure: Backend result set differs from expected SQL result.
- **F0177 (cold_cache, functional, GROUP_BY)**
  - NL: `Break down projects by project name where project name has at least 7 characters.`
  - Expected SQL: `SELECT project_name, COUNT(*) AS row_count FROM projects WHERE project_name IS NOT NULL AND LENGTH(project_name) >= 7 GROUP BY project_name ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT COUNT(*) FROM projects WHERE project_name LIKE '%_____%%'`
  - Executed SQL: `SELECT COUNT(*) FROM projects WHERE project_name LIKE '%_____%%'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['project_name', 'row_count'] sample=[{'project_name': 'Semantic Cache Optimization', 'row_count': 1}, {'project_name': 'Model Monitoring Rollout', 'row_count': 1}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 5}]
  - Failure: Backend result set differs from expected SQL result.
- **F0178 (cold_cache, functional, GROUP_BY)**
  - NL: `Count query history for each generation mode after filtering for generation mode has at least 8 characters.`
  - Expected SQL: `SELECT generation_mode, COUNT(*) AS row_count FROM query_history WHERE generation_mode IS NOT NULL AND LENGTH(generation_mode) >= 8 GROUP BY generation_mode ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT COUNT(*) 
FROM query_history 
WHERE natural_language_query LIKE '%filtering%'
AND generation_mode = 'after'`
  - Executed SQL: `SELECT COUNT(*) 
FROM query_history 
WHERE natural_language_query LIKE '%filtering%'
AND generation_mode = 'after'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['generation_mode', 'row_count'] sample=[]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0179 (cold_cache, functional, GROUP_BY)**
  - NL: `Summarize vendors grouped by vendor name with vendor name has at least 9 characters.`
  - Expected SQL: `SELECT vendor_name, COUNT(*) AS row_count FROM vendors WHERE vendor_name IS NOT NULL AND LENGTH(vendor_name) >= 9 GROUP BY vendor_name ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT vendor_name 
FROM vendors 
GROUP BY vendor_name 
HAVING LENGTH(vendor_name) >= 9`
  - Executed SQL: `SELECT vendor_name 
FROM vendors 
GROUP BY vendor_name 
HAVING LENGTH(vendor_name) >= 9`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['vendor_name', 'row_count'] sample=[{'vendor_name': 'Tech Vendors', 'row_count': 1}, {'vendor_name': 'Prime Distributors', 'row_count': 1}]
  - Actual Result: rows=4 columns=['vendor_name'] sample=[{'vendor_name': 'ABC Traders'}, {'vendor_name': 'Global Supplies'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0180 (cold_cache, functional, GROUP_BY)**
  - NL: `Break down authors by country where country has at least 10 characters.`
  - Expected SQL: `SELECT country, COUNT(*) AS row_count FROM authors WHERE country IS NOT NULL AND LENGTH(country) >= 10 GROUP BY country ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT author_id, COUNT(*) as count 
FROM authors 
WHERE LENGTH(country) >= 10 
GROUP BY author_id`
  - Executed SQL: `SELECT author_id, COUNT(*) as count 
FROM authors 
WHERE LENGTH(country) >= 10 
GROUP BY author_id`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['country', 'row_count'] sample=[{'country': 'Netherlands', 'row_count': 1}]
  - Actual Result: rows=1 columns=['author_id', 'count'] sample=[{'author_id': 3, 'count': 1}]
  - Failure: Backend result set differs from expected SQL result.
- **F0181 (cold_cache, functional, GROUP_BY)**
  - NL: `Count books for each title after filtering for title has at least 11 characters.`
  - Expected SQL: `SELECT title, COUNT(*) AS row_count FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 11 GROUP BY title ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT COUNT(*) , title FROM books WHERE LENGTH(title) >= 2 GROUP BY title`
  - Executed SQL: `SELECT COUNT(*) , title FROM books WHERE LENGTH(title) >= 2 GROUP BY title`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['title', 'row_count'] sample=[{'title': 'Refactoring', 'row_count': 1}, {'title': 'Modern Operating Systems', 'row_count': 1}]
  - Actual Result: rows=5 columns=['COUNT(*)', 'title'] sample=[{'COUNT(*)': 1, 'title': 'Clean Architecture'}, {'COUNT(*)': 1, 'title': 'Clean Code'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0184 (cold_cache, functional, GROUP_BY)**
  - NL: `Count employees for each email after filtering for email has at least 14 characters.`
  - Expected SQL: `SELECT email, COUNT(*) AS row_count FROM employees WHERE email IS NOT NULL AND LENGTH(email) >= 14 GROUP BY email ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT employee_id, COUNT(*) FROM employees WHERE LENGTH(email) >= 14 GROUP BY email`
  - Executed SQL: `SELECT employee_id, COUNT(*) FROM employees WHERE LENGTH(email) >= 14 GROUP BY email`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['email', 'row_count'] sample=[{'email': 'ava.thompson@company.com', 'row_count': 1}, {'email': 'daniel.martinez@company.com', 'row_count': 1}]
  - Actual Result: rows=8 columns=['employee_id', 'COUNT(*)'] sample=[{'employee_id': 126, 'COUNT(*)': 1}, {'employee_id': 115, 'COUNT(*)': 1}]
  - Failure: Backend result set differs from expected SQL result.
### Wrong aggregate function
- **F0122 (cold_cache, functional, AVG)**
  - NL: `Calculate the average author id for authors where author name has at least 19 characters.`
  - Expected SQL: `SELECT AVG(author_id) AS avg_author_id FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 19;`
  - Generated SQL: `SELECT CAST(SUM(author_id) AS REAL) / COUNT(*) FROM authors WHERE LENGTH(author_name) >= 1`
  - Executed SQL: `SELECT CAST(SUM(author_id) AS REAL) / COUNT(*) FROM authors WHERE LENGTH(author_name) >= 1`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['avg_author_id'] sample=[{'avg_author_id': None}]
  - Actual Result: rows=1 columns=['CAST(SUM(author_id) AS REAL) / COUNT(*)'] sample=[{'CAST(SUM(author_id) AS REAL) / COUNT(*)': 2.5}]
  - Failure: Backend result set differs from expected SQL result.
- **F0125 (cold_cache, functional, AVG)**
  - NL: `What is the average salary in employees where salary is at least 22?`
  - Expected SQL: `SELECT AVG(salary) AS avg_salary FROM employees WHERE salary >= 22;`
  - Generated SQL: `SELECT COUNT(*) FROM employees WHERE salary >= 22`
  - Executed SQL: `SELECT COUNT(*) FROM employees WHERE salary >= 22`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['avg_salary'] sample=[{'avg_salary': 74875.0}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 8}]
  - Failure: Backend result set differs from expected SQL result.
- **F0127 (cold_cache, functional, MIN)**
  - NL: `What is the lowest price in books where price is at least 1?`
  - Expected SQL: `SELECT MIN(price) AS min_price FROM books WHERE price >= 1;`
  - Generated SQL: `SELECT AVG(price) FROM books WHERE price >= 1`
  - Executed SQL: `SELECT AVG(price) FROM books WHERE price >= 1`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['min_price'] sample=[{'min_price': 650.0}]
  - Actual Result: rows=1 columns=['AVG(price)'] sample=[{'AVG(price)': 834.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0132 (cold_cache, functional, MIN)**
  - NL: `Calculate the lowest budget for projects where project name has at least 7 characters.`
  - Expected SQL: `SELECT MIN(budget) AS min_budget FROM projects WHERE project_name IS NOT NULL AND LENGTH(project_name) >= 7;`
  - Generated SQL: `SELECT AVG(budget) FROM projects WHERE LENGTH(project_name) >= 7`
  - Executed SQL: `SELECT AVG(budget) FROM projects WHERE LENGTH(project_name) >= 7`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['min_budget'] sample=[{'min_budget': 76000.0}]
  - Actual Result: rows=1 columns=['AVG(budget)'] sample=[{'AVG(budget)': 124300.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0139 (cold_cache, functional, MIN)**
  - NL: `What is the lowest salary in employees where salary is at least 13?`
  - Expected SQL: `SELECT MIN(salary) AS min_salary FROM employees WHERE salary >= 13;`
  - Generated SQL: `SELECT AVG(salary) FROM employees WHERE salary >= 13`
  - Executed SQL: `SELECT AVG(salary) FROM employees WHERE salary >= 13`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['min_salary'] sample=[{'min_salary': 48000}]
  - Actual Result: rows=1 columns=['AVG(salary)'] sample=[{'AVG(salary)': 74875.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0142 (cold_cache, functional, MAX)**
  - NL: `What is the highest price in books where price is at least 1?`
  - Expected SQL: `SELECT MAX(price) AS max_price FROM books WHERE price >= 1;`
  - Generated SQL: `SELECT AVG(price) FROM books WHERE price >= 1`
  - Executed SQL: `SELECT AVG(price) FROM books WHERE price >= 1`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['max_price'] sample=[{'max_price': 1200.0}]
  - Actual Result: rows=1 columns=['AVG(price)'] sample=[{'AVG(price)': 834.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0145 (cold_cache, functional, MAX)**
  - NL: `What is the highest salary in employees where salary is at least 4?`
  - Expected SQL: `SELECT MAX(salary) AS max_salary FROM employees WHERE salary >= 4;`
  - Generated SQL: `SELECT MIN(salary) FROM employees WHERE salary >= 4`
  - Executed SQL: `SELECT MIN(salary) FROM employees WHERE salary >= 4`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['max_salary'] sample=[{'max_salary': 99000}]
  - Actual Result: rows=1 columns=['MIN(salary)'] sample=[{'MIN(salary)': 48000}]
  - Failure: Backend result set differs from expected SQL result.
- **F0147 (cold_cache, functional, MAX)**
  - NL: `Calculate the highest budget for projects where project name has at least 7 characters.`
  - Expected SQL: `SELECT MAX(budget) AS max_budget FROM projects WHERE project_name IS NOT NULL AND LENGTH(project_name) >= 7;`
  - Generated SQL: `SELECT AVG(budget) FROM projects WHERE LENGTH(project_name) >= 7`
  - Executed SQL: `SELECT AVG(budget) FROM projects WHERE LENGTH(project_name) >= 7`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['max_budget'] sample=[{'max_budget': 185000.0}]
  - Actual Result: rows=1 columns=['AVG(budget)'] sample=[{'AVG(budget)': 124300.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0148 (cold_cache, functional, MAX)**
  - NL: `What is the highest rows returned in query history where rows returned is at least 7?`
  - Expected SQL: `SELECT MAX(rows_returned) AS max_rows_returned FROM query_history WHERE rows_returned >= 7;`
  - Generated SQL: `SELECT MIN(rows_returned) FROM query_history WHERE rows_returned >= 7`
  - Executed SQL: `SELECT MIN(rows_returned) FROM query_history WHERE rows_returned >= 7`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['max_rows_returned'] sample=[{'max_rows_returned': 1218}]
  - Actual Result: rows=1 columns=['MIN(rows_returned)'] sample=[{'MIN(rows_returned)': 7}]
  - Failure: Backend result set differs from expected SQL result.
- **F0152 (cold_cache, functional, MAX)**
  - NL: `Show the highest price value for books across all records.`
  - Expected SQL: `SELECT MAX(price) AS max_price FROM books;`
  - Generated SQL: `SELECT MIN(price) FROM books`
  - Executed SQL: `SELECT MIN(price) FROM books`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['max_price'] sample=[{'max_price': 1200.0}]
  - Actual Result: rows=1 columns=['MIN(price)'] sample=[{'MIN(price)': 650.0}]
  - Failure: Backend result set differs from expected SQL result.
### LIMIT clause mismatch
- **F0051 (cold_cache, functional, LIMIT)**
  - NL: `Show 3 authors records from this page.`
  - Expected SQL: `SELECT author_id FROM authors LIMIT 3 OFFSET 0;`
  - Generated SQL: `SELECT * FROM authors LIMIT 3`
  - Executed SQL: `SELECT * FROM authors LIMIT 3`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3 columns=['author_id'] sample=[{'author_id': 1}, {'author_id': 2}]
  - Actual Result: rows=3 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 1, 'author_name': 'Robert Martin', 'country': 'USA'}, {'author_id': 2, 'author_name': 'Martin Fowler', 'country': 'UK'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0052 (cold_cache, functional, LIMIT)**
  - NL: `Return a page of 4 books.`
  - Expected SQL: `SELECT title, author_id FROM books LIMIT 4 OFFSET 1;`
  - Generated SQL: `SELECT * FROM books LIMIT 4;`
  - Executed SQL: `SELECT * FROM books LIMIT 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['title', 'author_id'] sample=[{'title': 'Refactoring', 'author_id': 2}, {'title': 'Modern Operating Systems', 'author_id': 3}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0053 (cold_cache, functional, LIMIT)**
  - NL: `List the next 5 departments records.`
  - Expected SQL: `SELECT location, department_id, department_name FROM departments LIMIT 5 OFFSET 2;`
  - Generated SQL: `SELECT * FROM departments ORDER BY department_id LIMIT 5;`
  - Executed SQL: `SELECT * FROM departments ORDER BY department_id LIMIT 5;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3 columns=['location', 'department_id', 'department_name'] sample=[{'location': 'Chennai', 'department_id': 3, 'department_name': 'Finance'}, {'location': 'Hyderabad', 'department_id': 4, 'department_name': 'Marketing'}]
  - Actual Result: rows=5 columns=['department_id', 'department_name', 'location'] sample=[{'department_id': 1, 'department_name': 'IT', 'location': 'Bangalore'}, {'department_id': 2, 'department_name': 'HR', 'location': 'Mysore'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0055 (cold_cache, functional, LIMIT)**
  - NL: `Return a page of 7 employees.`
  - Expected SQL: `SELECT salary, joining_date FROM employees LIMIT 7 OFFSET 0;`
  - Generated SQL: `SELECT * FROM employees LIMIT 7;`
  - Executed SQL: `SELECT * FROM employees LIMIT 7;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=7 columns=['salary', 'joining_date'] sample=[{'salary': 75000, 'joining_date': '2019-07-18'}, {'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=7 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0056 (cold_cache, functional, LIMIT)**
  - NL: `List the next 3 products records.`
  - Expected SQL: `SELECT price, product_id, product_name FROM products LIMIT 3 OFFSET 1;`
  - Generated SQL: `SELECT * FROM products LIMIT 3`
  - Executed SQL: `SELECT * FROM products LIMIT 3`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['price', 'product_id', 'product_name'] sample=[{'price': 19.99, 'product_id': 2, 'product_name': 'Cache Booster'}]
  - Actual Result: rows=2 columns=['product_id', 'product_name', 'price'] sample=[{'product_id': 1, 'product_name': 'Analytics Pack', 'price': 49.99}, {'product_id': 2, 'product_name': 'Cache Booster', 'price': 19.99}]
  - Failure: Backend result set differs from expected SQL result.
- **F0057 (cold_cache, functional, LIMIT)**
  - NL: `Show 4 projects records from this page.`
  - Expected SQL: `SELECT project_id FROM projects LIMIT 4 OFFSET 2;`
  - Generated SQL: `SELECT * FROM projects LIMIT 4;`
  - Executed SQL: `SELECT * FROM projects LIMIT 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3 columns=['project_id'] sample=[{'project_id': 3}, {'project_id': 4}]
  - Actual Result: rows=4 columns=['project_id', 'project_name', 'budget'] sample=[{'project_id': 1, 'project_name': 'Semantic Cache Optimization', 'budget': 125000.0}, {'project_id': 2, 'project_name': 'LLM SQL Generation', 'budget': 185000.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0058 (cold_cache, functional, LIMIT)**
  - NL: `Return a page of 5 query history.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history LIMIT 5 OFFSET 3;`
  - Generated SQL: `SELECT * FROM query_history LIMIT 5`
  - Executed SQL: `SELECT * FROM query_history LIMIT 5`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 0, 'created_at': '2026-06-08 13:46:02.870911'}, {'rows_returned': 0, 'created_at': '2026-06-08 13:46:02.884030'}]
  - Actual Result: rows=5 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 1, 'natural_language_query': 'Show employees from Finance', 'generated_sql': "SELECT * FROM employees\nWHERE department = 'Finance';", 'generation_mode': 'Rule', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.1101, 'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'id': 2, 'natural_language_query': 'Show all vendors', 'generated_sql': 'SELECT * FROM vendors;', 'generation_mode': 'Llm', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.0345, 'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0060 (cold_cache, functional, LIMIT)**
  - NL: `Show 7 authors records from this page.`
  - Expected SQL: `SELECT author_id FROM authors LIMIT 7 OFFSET 1;`
  - Generated SQL: `SELECT * FROM authors LIMIT 7`
  - Executed SQL: `SELECT * FROM authors LIMIT 7`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3 columns=['author_id'] sample=[{'author_id': 2}, {'author_id': 3}]
  - Actual Result: rows=4 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 1, 'author_name': 'Robert Martin', 'country': 'USA'}, {'author_id': 2, 'author_name': 'Martin Fowler', 'country': 'UK'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0061 (cold_cache, functional, LIMIT)**
  - NL: `Return a page of 3 books.`
  - Expected SQL: `SELECT author_id, price FROM books LIMIT 3 OFFSET 2;`
  - Generated SQL: `SELECT * FROM books LIMIT 4;`
  - Executed SQL: `SELECT * FROM books LIMIT 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3 columns=['author_id', 'price'] sample=[{'author_id': 3, 'price': 900.0}, {'author_id': 4, 'price': 1200.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0062 (cold_cache, functional, LIMIT)**
  - NL: `List the next 4 departments records.`
  - Expected SQL: `SELECT location, department_id, department_name FROM departments LIMIT 4 OFFSET 3;`
  - Generated SQL: `SELECT * FROM departments ORDER BY department_id LIMIT 5;`
  - Executed SQL: `SELECT * FROM departments ORDER BY department_id LIMIT 5;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=2 columns=['location', 'department_id', 'department_name'] sample=[{'location': 'Hyderabad', 'department_id': 4, 'department_name': 'Marketing'}, {'location': 'Pune', 'department_id': 5, 'department_name': 'Research'}]
  - Actual Result: rows=5 columns=['department_id', 'department_name', 'location'] sample=[{'department_id': 1, 'department_name': 'IT', 'location': 'Bangalore'}, {'department_id': 2, 'department_name': 'HR', 'location': 'Mysore'}]
  - Failure: Backend result set differs from expected SQL result.
### WHERE clause error
- **F0016 (cold_cache, functional, WHERE)**
  - NL: `Show authors where author name has at least 1 characters.`
  - Expected SQL: `SELECT author_id FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1;`
  - Generated SQL: `SELECT * FROM authors WHERE LENGTH(author_name) >= 1`
  - Executed SQL: `SELECT * FROM authors WHERE LENGTH(author_name) >= 1`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_id'] sample=[{'author_id': 1}, {'author_id': 2}]
  - Actual Result: rows=4 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 1, 'author_name': 'Robert Martin', 'country': 'USA'}, {'author_id': 2, 'author_name': 'Martin Fowler', 'country': 'UK'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0017 (cold_cache, functional, WHERE)**
  - NL: `Show books with price greater than 1.`
  - Expected SQL: `SELECT title, author_id FROM books WHERE price >= 1;`
  - Generated SQL: `SELECT * FROM books WHERE price > 1;`
  - Executed SQL: `SELECT * FROM books WHERE price > 1;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['title', 'author_id'] sample=[{'title': 'Clean Code', 'author_id': 1}, {'title': 'Refactoring', 'author_id': 2}]
  - Actual Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0018 (cold_cache, functional, WHERE)**
  - NL: `Show departments where department name has at least 3 characters.`
  - Expected SQL: `SELECT location, department_id, department_name FROM departments WHERE department_name IS NOT NULL AND LENGTH(department_name) >= 3;`
  - Generated SQL: `SELECT * FROM departments WHERE department_name >= '3'`
  - Executed SQL: `SELECT * FROM departments WHERE department_name >= '3'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3 columns=['location', 'department_id', 'department_name'] sample=[{'location': 'Chennai', 'department_id': 3, 'department_name': 'Finance'}, {'location': 'Hyderabad', 'department_id': 4, 'department_name': 'Marketing'}]
  - Actual Result: rows=5 columns=['department_id', 'department_name', 'location'] sample=[{'department_id': 1, 'department_name': 'IT', 'location': 'Bangalore'}, {'department_id': 2, 'department_name': 'HR', 'location': 'Mysore'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0020 (cold_cache, functional, WHERE)**
  - NL: `Show employees with salary less than 4.`
  - Expected SQL: `SELECT salary, joining_date FROM employees WHERE salary >= 4;`
  - Generated SQL: `SELECT * FROM employees WHERE salary < 4;`
  - Executed SQL: `SELECT * FROM employees WHERE salary < 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['salary', 'joining_date'] sample=[{'salary': 75000, 'joining_date': '2019-07-18'}, {'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=0 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0022 (cold_cache, functional, WHERE)**
  - NL: `Show projects with budget at least 6.`
  - Expected SQL: `SELECT project_id FROM projects WHERE budget >= 6;`
  - Generated SQL: `SELECT * FROM projects WHERE budget >= 6;`
  - Executed SQL: `SELECT * FROM projects WHERE budget >= 6;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['project_id'] sample=[{'project_id': 1}, {'project_id': 2}]
  - Actual Result: rows=5 columns=['project_id', 'project_name', 'budget'] sample=[{'project_id': 1, 'project_name': 'Semantic Cache Optimization', 'budget': 125000.0}, {'project_id': 2, 'project_name': 'LLM SQL Generation', 'budget': 185000.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0023 (cold_cache, functional, WHERE)**
  - NL: `Show query history with rows returned greater than 7.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history WHERE rows_returned >= 7;`
  - Generated SQL: `SELECT * FROM query_history WHERE rows_returned > 7`
  - Executed SQL: `SELECT * FROM query_history WHERE rows_returned > 7`
  - Validation: `valid` errors=[]
  - Expected Result: rows=183 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 8, 'created_at': '2026-07-01 17:13:54.870163'}, {'rows_returned': 8, 'created_at': '2026-07-03 17:29:46.498401'}]
  - Actual Result: rows=174 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 28, 'natural_language_query': 'show all employees', 'generated_sql': 'SELECT * FROM employees;', 'generation_mode': 'LLM', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.5616, 'rows_returned': 8, 'created_at': '2026-07-01 17:13:54.870163'}, {'id': 54, 'natural_language_query': 'Show employee age', 'generated_sql': "SELECT DATE('now') - employees.joining_date AS age FROM employees", 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.6566, 'rows_returned': 8, 'created_at': '2026-07-03 17:29:46.498401'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0025 (cold_cache, functional, WHERE)**
  - NL: `Show authors where country has at least 10 characters.`
  - Expected SQL: `SELECT author_id FROM authors WHERE country IS NOT NULL AND LENGTH(country) >= 10;`
  - Generated SQL: `SELECT * FROM authors WHERE LENGTH(country) >= 10`
  - Executed SQL: `SELECT * FROM authors WHERE LENGTH(country) >= 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['author_id'] sample=[{'author_id': 3}]
  - Actual Result: rows=1 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 3, 'author_name': 'Andrew Tanenbaum', 'country': 'Netherlands'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0026 (cold_cache, functional, WHERE)**
  - NL: `Show books with author id less than 10.`
  - Expected SQL: `SELECT author_id, price FROM books WHERE author_id >= 10;`
  - Generated SQL: `SELECT * FROM books WHERE author_id < 10;`
  - Executed SQL: `SELECT * FROM books WHERE author_id < 10;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['author_id', 'price'] sample=[]
  - Actual Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0029 (cold_cache, functional, WHERE)**
  - NL: `Show employees with salary greater than 13.`
  - Expected SQL: `SELECT name, email FROM employees WHERE salary >= 13;`
  - Generated SQL: `SELECT * FROM employees WHERE salary > 13;`
  - Executed SQL: `SELECT * FROM employees WHERE salary > 13;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['name', 'email'] sample=[{'name': 'David Wilson', 'email': 'david.wilson@company.com'}, {'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com'}]
  - Actual Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0031 (cold_cache, functional, WHERE)**
  - NL: `Show projects with budget below 15.`
  - Expected SQL: `SELECT project_id FROM projects WHERE budget >= 15;`
  - Generated SQL: `SELECT * FROM projects WHERE budget < 15;`
  - Executed SQL: `SELECT * FROM projects WHERE budget < 15;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['project_id'] sample=[{'project_id': 1}, {'project_id': 2}]
  - Actual Result: rows=0 columns=['project_id', 'project_name', 'budget'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
### ORDER BY mismatch
- **F0036 (cold_cache, functional, ORDER_BY)**
  - NL: `List the first 5 authors ordered by author id ascending.`
  - Expected SQL: `SELECT author_id FROM authors ORDER BY author_id ASC LIMIT 5;`
  - Generated SQL: `SELECT * FROM authors ORDER BY author_id ASC LIMIT 5`
  - Executed SQL: `SELECT * FROM authors ORDER BY author_id ASC LIMIT 5`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_id'] sample=[{'author_id': 1}, {'author_id': 2}]
  - Actual Result: rows=4 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 1, 'author_name': 'Robert Martin', 'country': 'USA'}, {'author_id': 2, 'author_name': 'Martin Fowler', 'country': 'UK'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0037 (cold_cache, functional, ORDER_BY)**
  - NL: `Show 6 books sorted by title in descending order.`
  - Expected SQL: `SELECT title, author_id FROM books ORDER BY title DESC LIMIT 6;`
  - Generated SQL: `SELECT * FROM books ORDER BY title DESC LIMIT 6`
  - Executed SQL: `SELECT * FROM books ORDER BY title DESC LIMIT 6`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['title', 'author_id'] sample=[{'title': 'Refactoring', 'author_id': 2}, {'title': 'Modern Operating Systems', 'author_id': 3}]
  - Actual Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}, {'book_id': 3, 'title': 'Modern Operating Systems', 'author_id': 3, 'price': 900.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0038 (cold_cache, functional, ORDER_BY)**
  - NL: `Return 7 departments ranked by location ascending.`
  - Expected SQL: `SELECT location, department_id, department_name FROM departments ORDER BY location ASC LIMIT 7;`
  - Generated SQL: `SELECT department_id FROM departments ORDER BY location ASC LIMIT 7`
  - Executed SQL: `SELECT department_id FROM departments ORDER BY location ASC LIMIT 7`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['location', 'department_id', 'department_name'] sample=[{'location': 'Bangalore', 'department_id': 1, 'department_name': 'IT'}, {'location': 'Chennai', 'department_id': 3, 'department_name': 'Finance'}]
  - Actual Result: rows=5 columns=['department_id'] sample=[{'department_id': 1}, {'department_id': 3}]
  - Failure: Backend result set differs from expected SQL result.
- **F0040 (cold_cache, functional, ORDER_BY)**
  - NL: `Show 9 employees sorted by salary in ascending order.`
  - Expected SQL: `SELECT salary, joining_date FROM employees ORDER BY salary ASC LIMIT 9;`
  - Generated SQL: `SELECT * FROM employees ORDER BY salary ASC LIMIT 9;`
  - Executed SQL: `SELECT * FROM employees ORDER BY salary ASC LIMIT 9;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['salary', 'joining_date'] sample=[{'salary': 48000, 'joining_date': '2022-04-03'}, {'salary': 54000, 'joining_date': '2023-02-06'}]
  - Actual Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 131, 'name': 'Noah Garcia', 'email': 'noah.garcia@company.com', 'department': 'Operations', 'salary': 48000, 'joining_date': '2022-04-03'}, {'employee_id': 121, 'name': 'Priya Raman', 'email': 'priya.raman@company.com', 'department': 'Human Resources', 'salary': 54000, 'joining_date': '2023-02-06'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0042 (cold_cache, functional, ORDER_BY)**
  - NL: `List the first 11 projects ordered by project id ascending.`
  - Expected SQL: `SELECT project_id FROM projects ORDER BY project_id ASC LIMIT 11;`
  - Generated SQL: `SELECT * FROM projects ORDER BY project_id ASC LIMIT 11`
  - Executed SQL: `SELECT * FROM projects ORDER BY project_id ASC LIMIT 11`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['project_id'] sample=[{'project_id': 1}, {'project_id': 2}]
  - Actual Result: rows=5 columns=['project_id', 'project_name', 'budget'] sample=[{'project_id': 1, 'project_name': 'Semantic Cache Optimization', 'budget': 125000.0}, {'project_id': 2, 'project_name': 'LLM SQL Generation', 'budget': 185000.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0043 (cold_cache, functional, ORDER_BY)**
  - NL: `Show 12 query history sorted by rows returned in descending order.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history ORDER BY rows_returned DESC LIMIT 12;`
  - Generated SQL: `SELECT * FROM query_history ORDER BY rows_returned DESC LIMIT 12`
  - Executed SQL: `SELECT * FROM query_history ORDER BY rows_returned DESC LIMIT 12`
  - Validation: `valid` errors=[]
  - Expected Result: rows=12 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 1218, 'created_at': '2026-07-05 15:50:20.309533'}, {'rows_returned': 1218, 'created_at': '2026-07-05 15:56:19.302383'}]
  - Actual Result: rows=12 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 1246, 'natural_language_query': 'Return the grouped query history totals.', 'generated_sql': 'SELECT COUNT(*) AS total_queries FROM query_history GROUP BY natural_language_query', 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.5988, 'rows_returned': 1218, 'created_at': '2026-07-05 15:50:20.309533'}, {'id': 3130, 'natural_language_query': 'Return the grouped query history totals.', 'generated_sql': 'SELECT COUNT(*) AS total_queries FROM query_history GROUP BY natural_language_query', 'generation_mode': 'LLM', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.106, 'rows_returned': 1218, 'created_at': '2026-07-05 15:56:19.302383'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0044 (cold_cache, functional, ORDER_BY)**
  - NL: `Return 13 vendors ranked by id ascending.`
  - Expected SQL: `SELECT id, vendor_name, city FROM vendors ORDER BY id ASC LIMIT 13;`
  - Generated SQL: `SELECT * FROM vendors ORDER BY id ASC LIMIT 13`
  - Executed SQL: `SELECT * FROM vendors ORDER BY id ASC LIMIT 13`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['id', 'vendor_name', 'city'] sample=[{'id': 1, 'vendor_name': 'ABC Traders', 'city': 'Bangalore'}, {'id': 2, 'vendor_name': 'Global Supplies', 'city': 'Chennai'}]
  - Actual Result: rows=4 columns=['id', 'vendor_name', 'city', 'rating'] sample=[{'id': 1, 'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'id': 2, 'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Failure: Backend result set differs from expected SQL result.
- **F0045 (cold_cache, functional, ORDER_BY)**
  - NL: `List the first 14 authors ordered by author id descending.`
  - Expected SQL: `SELECT author_id FROM authors ORDER BY author_id DESC LIMIT 14;`
  - Generated SQL: `SELECT * FROM authors ORDER BY author_id DESC LIMIT 14`
  - Executed SQL: `SELECT * FROM authors ORDER BY author_id DESC LIMIT 14`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_id'] sample=[{'author_id': 4}, {'author_id': 3}]
  - Actual Result: rows=4 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 4, 'author_name': 'Ian Goodfellow', 'country': 'USA'}, {'author_id': 3, 'author_name': 'Andrew Tanenbaum', 'country': 'Netherlands'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0046 (cold_cache, functional, ORDER_BY)**
  - NL: `Show 15 books sorted by author id in ascending order.`
  - Expected SQL: `SELECT author_id, price FROM books ORDER BY author_id ASC LIMIT 15;`
  - Generated SQL: `SELECT * FROM books ORDER BY author_id ASC LIMIT 15`
  - Executed SQL: `SELECT * FROM books ORDER BY author_id ASC LIMIT 15`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['author_id', 'price'] sample=[{'author_id': 1, 'price': 650.0}, {'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0047 (cold_cache, functional, ORDER_BY)**
  - NL: `Return 16 departments ranked by location descending.`
  - Expected SQL: `SELECT location, department_id, department_name FROM departments ORDER BY location DESC LIMIT 16;`
  - Generated SQL: `SELECT department_id FROM departments ORDER BY location ASC LIMIT 7`
  - Executed SQL: `SELECT department_id FROM departments ORDER BY location ASC LIMIT 7`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['location', 'department_id', 'department_name'] sample=[{'location': 'Pune', 'department_id': 5, 'department_name': 'Research'}, {'location': 'Mysore', 'department_id': 2, 'department_name': 'HR'}]
  - Actual Result: rows=5 columns=['department_id'] sample=[{'department_id': 1}, {'department_id': 3}]
  - Failure: Backend result set differs from expected SQL result.
### Aggregate result mismatch
- **F0092 (cold_cache, functional, COUNT)**
  - NL: `Return the number of departments after filtering for location has at least 12 characters.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM departments WHERE location IS NOT NULL AND LENGTH(location) >= 12;`
  - Generated SQL: `SELECT COUNT(*)
FROM departments
WHERE LENGTH(location) >= 3`
  - Executed SQL: `SELECT COUNT(*)
FROM departments
WHERE LENGTH(location) >= 3`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 5}]
  - Failure: Backend result set differs from expected SQL result.
- **F0101 (cold_cache, functional, COUNT)**
  - NL: `Return the number of departments after filtering for location has at least 21 characters.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM departments WHERE location IS NOT NULL AND LENGTH(location) >= 21;`
  - Generated SQL: `SELECT COUNT(*)
FROM departments
WHERE LENGTH(location) >= 3`
  - Executed SQL: `SELECT COUNT(*)
FROM departments
WHERE LENGTH(location) >= 3`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 5}]
  - Failure: Backend result set differs from expected SQL result.
- **S0402 (cold_cache, semantic, COUNT)**
  - NL: `How many authors match this request?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM authors WHERE author_id >= 0;`
  - Generated SQL: `SELECT COUNT(author_id) FROM authors WHERE author_id = 'this'`
  - Executed SQL: `SELECT COUNT(author_id) FROM authors WHERE author_id = 'this'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 4}]
  - Actual Result: rows=1 columns=['COUNT(author_id)'] sample=[{'COUNT(author_id)': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **S0407 (cold_cache, semantic, COUNT)**
  - NL: `How many books match this request?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 2;`
  - Generated SQL: `SELECT COUNT(*) FROM books WHERE author_id = 'this'`
  - Executed SQL: `SELECT COUNT(*) FROM books WHERE author_id = 'this'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 5}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **S0412 (cold_cache, semantic, COUNT)**
  - NL: `How many departments match this request?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM departments WHERE location IS NOT NULL AND LENGTH(location) >= 3;`
  - Generated SQL: `SELECT COUNT(department_id) FROM departments WHERE department_name = 'this'`
  - Executed SQL: `SELECT COUNT(department_id) FROM departments WHERE department_name = 'this'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 5}]
  - Actual Result: rows=1 columns=['COUNT(department_id)'] sample=[{'COUNT(department_id)': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **S0422 (cold_cache, semantic, COUNT)**
  - NL: `How many employees match this request?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM employees WHERE salary >= 4;`
  - Generated SQL: `SELECT COUNT(*) FROM employees WHERE department = 'this'`
  - Executed SQL: `SELECT COUNT(*) FROM employees WHERE department = 'this'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 8}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **S0427 (cold_cache, semantic, COUNT)**
  - NL: `How many products match this request?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM products WHERE price >= 5;`
  - Generated SQL: `SELECT COUNT(*) FROM products WHERE product_name LIKE '%match%' AND price > 10`
  - Executed SQL: `SELECT COUNT(*) FROM products WHERE product_name LIKE '%match%' AND price > 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 2}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **S0431 (cold_cache, semantic, COUNT)**
  - NL: `Count the projects.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM projects WHERE project_id >= 6;`
  - Generated SQL: `SELECT COUNT(project_id) FROM projects;`
  - Executed SQL: `SELECT COUNT(project_id) FROM projects;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=1 columns=['COUNT(project_id)'] sample=[{'COUNT(project_id)': 5}]
  - Failure: Backend result set differs from expected SQL result.
- **S0433 (cold_cache, semantic, COUNT)**
  - NL: `Return the number of projects.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM projects WHERE project_id >= 6;`
  - Generated SQL: `SELECT COUNT(*) FROM projects`
  - Executed SQL: `SELECT COUNT(*) FROM projects`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=1 columns=['COUNT(*)'] sample=[{'COUNT(*)': 5}]
  - Failure: Backend result set differs from expected SQL result.
- **S0434 (cold_cache, semantic, COUNT)**
  - NL: `Please calculate the projects count.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM projects WHERE project_id >= 6;`
  - Generated SQL: `SELECT COUNT(project_id) FROM projects;`
  - Executed SQL: `SELECT COUNT(project_id) FROM projects;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=1 columns=['COUNT(project_id)'] sample=[{'COUNT(project_id)': 5}]
  - Failure: Backend result set differs from expected SQL result.
### DISTINCT/projection mismatch
- **F0066 (cold_cache, functional, DISTINCT)**
  - NL: `List unique author name values from authors where author name has at least 1 characters.`
  - Expected SQL: `SELECT DISTINCT author_name FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1 ORDER BY author_name ASC;`
  - Generated SQL: `SELECT DISTINCT author_name FROM authors WHERE LENGTH(author_name) > 0`
  - Executed SQL: `SELECT DISTINCT author_name FROM authors WHERE LENGTH(author_name) > 0`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Andrew Tanenbaum'}, {'author_name': 'Ian Goodfellow'}]
  - Actual Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Robert Martin'}, {'author_name': 'Martin Fowler'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0067 (cold_cache, functional, DISTINCT)**
  - NL: `Show distinct title in books after filtering for title has at least 2 characters.`
  - Expected SQL: `SELECT DISTINCT title FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 2 ORDER BY title ASC;`
  - Generated SQL: `SELECT DISTINCT title FROM books WHERE LENGTH(title) >= 2`
  - Executed SQL: `SELECT DISTINCT title FROM books WHERE LENGTH(title) >= 2`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['title'] sample=[{'title': 'Clean Architecture'}, {'title': 'Clean Code'}]
  - Actual Result: rows=5 columns=['title'] sample=[{'title': 'Clean Code'}, {'title': 'Refactoring'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0072 (cold_cache, functional, DISTINCT)**
  - NL: `List unique project name values from projects where project name has at least 7 characters.`
  - Expected SQL: `SELECT DISTINCT project_name FROM projects WHERE project_name IS NOT NULL AND LENGTH(project_name) >= 7 ORDER BY project_name ASC;`
  - Generated SQL: `SELECT DISTINCT project_name 
FROM projects 
WHERE LENGTH(project_name) >= 7;`
  - Executed SQL: `SELECT DISTINCT project_name 
FROM projects 
WHERE LENGTH(project_name) >= 7;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['project_name'] sample=[{'project_name': 'Analytics Dashboard Refresh'}, {'project_name': 'Database Explorer Upgrade'}]
  - Actual Result: rows=5 columns=['project_name'] sample=[{'project_name': 'Semantic Cache Optimization'}, {'project_name': 'LLM SQL Generation'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0076 (cold_cache, functional, DISTINCT)**
  - NL: `Show distinct title in books after filtering for title has at least 11 characters.`
  - Expected SQL: `SELECT DISTINCT title FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 11 ORDER BY title ASC;`
  - Generated SQL: `SELECT DISTINCT title FROM books WHERE LENGTH(title) >= 2`
  - Executed SQL: `SELECT DISTINCT title FROM books WHERE LENGTH(title) >= 2`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['title'] sample=[{'title': 'Clean Architecture'}, {'title': 'Deep Learning'}]
  - Actual Result: rows=5 columns=['title'] sample=[{'title': 'Clean Code'}, {'title': 'Refactoring'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0080 (cold_cache, functional, DISTINCT)**
  - NL: `Which different product name values exist for products with product name has at least 15 characters?`
  - Expected SQL: `SELECT DISTINCT product_name FROM products WHERE product_name IS NOT NULL AND LENGTH(product_name) >= 15 ORDER BY product_name ASC;`
  - Generated SQL: `SELECT DISTINCT product_name 
FROM products 
WHERE LENGTH(product_name) >= 6`
  - Executed SQL: `SELECT DISTINCT product_name 
FROM products 
WHERE LENGTH(product_name) >= 6`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['product_name'] sample=[]
  - Actual Result: rows=2 columns=['product_name'] sample=[{'product_name': 'Analytics Pack'}, {'product_name': 'Cache Booster'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0326 (cold_cache, semantic, DISTINCT)**
  - NL: `List the unique author name for authors.`
  - Expected SQL: `SELECT DISTINCT author_name FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1 ORDER BY author_name ASC;`
  - Generated SQL: `SELECT DISTINCT author_name FROM authors`
  - Executed SQL: `SELECT DISTINCT author_name FROM authors`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Andrew Tanenbaum'}, {'author_name': 'Ian Goodfellow'}]
  - Actual Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Robert Martin'}, {'author_name': 'Martin Fowler'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0327 (cold_cache, semantic, DISTINCT)**
  - NL: `Show distinct author name for authors.`
  - Expected SQL: `SELECT DISTINCT author_name FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1 ORDER BY author_name ASC;`
  - Generated SQL: `SELECT DISTINCT author_name FROM authors`
  - Executed SQL: `SELECT DISTINCT author_name FROM authors`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Andrew Tanenbaum'}, {'author_name': 'Ian Goodfellow'}]
  - Actual Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Robert Martin'}, {'author_name': 'Martin Fowler'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0328 (cold_cache, semantic, DISTINCT)**
  - NL: `Which different author name for authors exist?`
  - Expected SQL: `SELECT DISTINCT author_name FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1 ORDER BY author_name ASC;`
  - Generated SQL: `SELECT DISTINCT author_name FROM authors WHERE author_name != ''`
  - Executed SQL: `SELECT DISTINCT author_name FROM authors WHERE author_name != ''`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Andrew Tanenbaum'}, {'author_name': 'Ian Goodfellow'}]
  - Actual Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Robert Martin'}, {'author_name': 'Martin Fowler'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0329 (cold_cache, semantic, DISTINCT)**
  - NL: `Return every unique author name for authors.`
  - Expected SQL: `SELECT DISTINCT author_name FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1 ORDER BY author_name ASC;`
  - Generated SQL: `SELECT DISTINCT author_name FROM authors`
  - Executed SQL: `SELECT DISTINCT author_name FROM authors`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Andrew Tanenbaum'}, {'author_name': 'Ian Goodfellow'}]
  - Actual Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Robert Martin'}, {'author_name': 'Martin Fowler'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0330 (cold_cache, semantic, DISTINCT)**
  - NL: `Please display deduplicated author name for authors.`
  - Expected SQL: `SELECT DISTINCT author_name FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1 ORDER BY author_name ASC;`
  - Generated SQL: `SELECT DISTINCT author_name FROM authors`
  - Executed SQL: `SELECT DISTINCT author_name FROM authors`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Andrew Tanenbaum'}, {'author_name': 'Ian Goodfellow'}]
  - Actual Result: rows=4 columns=['author_name'] sample=[{'author_name': 'Robert Martin'}, {'author_name': 'Martin Fowler'}]
  - Failure: Backend result set differs from expected SQL result.
### JOIN result mismatch
- **F0221 (cold_cache, functional, JOIN)**
  - NL: `Show up to 10 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE authors.author_id IS NOT NULL ORDER BY books.author_id ASC LIMIT 10;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0224 (cold_cache, functional, JOIN)**
  - NL: `Show up to 13 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE authors.author_id IS NOT NULL ORDER BY books.author_id ASC LIMIT 13;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0227 (cold_cache, functional, JOIN)**
  - NL: `Show up to 16 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL) ORDER BY books.author_id ASC LIMIT 16;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0230 (cold_cache, functional, JOIN)**
  - NL: `Show up to 19 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL) ORDER BY books.author_id ASC LIMIT 19;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0233 (cold_cache, functional, JOIN)**
  - NL: `Show up to 22 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL) ORDER BY books.author_id ASC LIMIT 22;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0236 (cold_cache, functional, JOIN)**
  - NL: `Show up to 25 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL) ORDER BY books.author_id ASC LIMIT 25;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0239 (cold_cache, functional, JOIN)**
  - NL: `Show up to 28 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL) ORDER BY books.author_id ASC LIMIT 28;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0242 (cold_cache, functional, JOIN)**
  - NL: `Show up to 31 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL) ORDER BY books.author_id ASC LIMIT 31;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0245 (cold_cache, functional, JOIN)**
  - NL: `Show up to 34 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL) ORDER BY books.author_id ASC LIMIT 34;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0248 (cold_cache, functional, JOIN)**
  - NL: `Show up to 37 books with their related authors.`
  - Expected SQL: `SELECT books.*, authors.author_id FROM books JOIN authors ON books.author_id = authors.author_id WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL) ORDER BY books.author_id ASC LIMIT 37;`
  - Generated SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Executed SQL: `SELECT * FROM books WHERE book_id IN ( SELECT author_id FROM authors ) LIMIT 10`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price', 'author_id'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}]
  - Actual Result: rows=4 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Failure: Backend result set differs from expected SQL result.
### Invalid query accepted via cached valid SQL
- **I0037 (cold_cache, invalid, None)**
  - NL: `Show records from the missing authors archive 36`
  - Expected SQL: `SELECT * FROM missing_authors_36;`
  - Generated SQL: `SELECT * FROM authors WHERE author_id = 0`
  - Executed SQL: `SELECT * FROM authors WHERE author_id = 0`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0043 (cold_cache, invalid, None)**
  - NL: `Show records from the missing vendors archive 44`
  - Expected SQL: `SELECT * FROM missing_vendors_44;`
  - Generated SQL: `SELECT * FROM vendors WHERE id = 'archive' AND vendor_name = 'missing' LIMIT 8;`
  - Executed SQL: `SELECT * FROM vendors WHERE id = 'archive' AND vendor_name = 'missing' LIMIT 8;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['id', 'vendor_name', 'city', 'rating'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0046 (cold_cache, invalid, None)**
  - NL: `Show records from the missing employee_projects archive 48`
  - Expected SQL: `SELECT * FROM missing_employee_projects_48;`
  - Generated SQL: `SELECT * FROM employee_projects WHERE role = 'archive' AND hours_per_week = 12;`
  - Executed SQL: `SELECT * FROM employee_projects WHERE role = 'archive' AND hours_per_week = 12;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0049 (cold_cache, invalid, None)**
  - NL: `Show records from the missing query_history archive 52`
  - Expected SQL: `SELECT * FROM missing_query_history_52;`
  - Generated SQL: `SELECT * FROM query_history WHERE natural_language_query = 'missing' AND generated_sql IS NULL AND execution_time > 16`
  - Executed SQL: `SELECT * FROM query_history WHERE natural_language_query = 'missing' AND generated_sql IS NULL AND execution_time > 16`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0052 (cold_cache, invalid, None)**
  - NL: `Show records from the missing departments archive 56`
  - Expected SQL: `SELECT * FROM missing_departments_56;`
  - Generated SQL: `SELECT * FROM departments WHERE department_id = 'archive' AND department_name = 'missing' LIMIT 20;`
  - Executed SQL: `SELECT * FROM departments WHERE department_id = 'archive' AND department_name = 'missing' LIMIT 20;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['department_id', 'department_name', 'location'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0053 (cold_cache, invalid, None)**
  - NL: `Show the missing column 57 for employee_projects`
  - Expected SQL: `SELECT missing_column_57 FROM employee_projects;`
  - Generated SQL: `SELECT * FROM employee_projects WHERE role = 'missing' AND hours_per_week = 21`
  - Executed SQL: `SELECT * FROM employee_projects WHERE role = 'missing' AND hours_per_week = 21`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0054 (cold_cache, invalid, None)**
  - NL: `Join products with projects using unavailable key pair 59`
  - Expected SQL: `SELECT * FROM products JOIN projects ON products.missing_id_59 = projects.missing_id_59;`
  - Generated SQL: `SELECT * FROM products JOIN projects ON products.product_id = projects.project_id WHERE (products.product_id , projects.project_id) = (23, 23)`
  - Executed SQL: `SELECT * FROM products JOIN projects ON products.product_id = projects.project_id WHERE (products.product_id , projects.project_id) = (23, 23)`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['product_id', 'product_name', 'price', 'project_id', 'project_name', 'budget'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0055 (cold_cache, invalid, None)**
  - NL: `Show records from the missing projects archive 60`
  - Expected SQL: `SELECT * FROM missing_projects_60;`
  - Generated SQL: `SELECT * FROM projects WHERE project_id = 'archive' AND budget = 24`
  - Executed SQL: `SELECT * FROM projects WHERE project_id = 'archive' AND budget = 24`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['project_id', 'project_name', 'budget'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0061 (cold_cache, invalid, None)**
  - NL: `Show records from the missing products archive 68`
  - Expected SQL: `SELECT * FROM missing_products_68;`
  - Generated SQL: `SELECT * FROM vendors WHERE id = 32`
  - Executed SQL: `SELECT * FROM vendors WHERE id = 32`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['id', 'vendor_name', 'city', 'rating'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0063 (cold_cache, invalid, None)**
  - NL: `Join vendors with authors using unavailable key pair 71`
  - Expected SQL: `SELECT * FROM vendors JOIN authors ON vendors.missing_id_71 = authors.missing_id_71;`
  - Generated SQL: `SELECT * FROM vendors AS T1 INNER JOIN authors AS T2 ON T1.id = 'unavailable' AND T2.author_id = 35`
  - Executed SQL: `SELECT * FROM vendors AS T1 INNER JOIN authors AS T2 ON T1.id = 'unavailable' AND T2.author_id = 35`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['id', 'vendor_name', 'city', 'rating', 'author_id', 'author_name', 'country'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
### SQL syntax error
- **F0267 (cold_cache, functional, HAVING)**
  - NL: `List generated sql groups in query history whose counts exceed 16.`
  - Expected SQL: `SELECT generated_sql, COUNT(*) AS row_count FROM query_history WHERE generated_sql IS NOT NULL AND LENGTH(generated_sql) >= 17 GROUP BY generated_sql HAVING COUNT(*) > 16 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT sql FROM query_history WHERE groups IN ( SELECT group_id FROM ... ) AND counts > 16`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Expected table name but got <Token token_type: TokenType.R_PAREN, text: ), line: 1, col: 74, start: 73, end: 73, comments: []>. Line 1, Col: 74.\n  SELECT sql FROM query_history WHERE groups IN ( SELECT group_id FROM ... \x1b[4m)\x1b[0m AND counts > 16']
  - Expected Result: rows=35 columns=['generated_sql', 'row_count'] sample=[{'generated_sql': 'SELECT *, ( SELECT author_id FROM authors WHERE id = authors.author_id ) AS related_author_id \nFROM books \nWHERE book_id IN ( SELECT book_id FROM books LIMIT 13 );', 'row_count': 37}, {'generated_sql': 'SELECT MIN(budget) FROM projects WHERE LENGTH(project_name) >= 16', 'row_count': 31}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0179 (cold_cache, semantic, ORDER_BY)**
  - NL: `Please display authors sorted as specified.`
  - Expected SQL: `SELECT author_id FROM authors ORDER BY author_id ASC LIMIT 5;`
  - Generated SQL: `SELECT * FROM authors ORDER BY authors AS specified`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Invalid expression / Unexpected token. Line 1, Col: 41.\n  SELECT * FROM authors ORDER BY authors \x1b[4mAS\x1b[0m specified']
  - Expected Result: rows=4 columns=['author_id'] sample=[{'author_id': 1}, {'author_id': 2}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0189 (cold_cache, semantic, ORDER_BY)**
  - NL: `Please display departments sorted as specified.`
  - Expected SQL: `SELECT location, department_id, department_name FROM departments ORDER BY location ASC LIMIT 7;`
  - Generated SQL: `SELECT * FROM departments ORDER BY department_id AS specified`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Invalid expression / Unexpected token. Line 1, Col: 51.\n  SELECT * FROM departments ORDER BY department_id \x1b[4mAS\x1b[0m specified']
  - Expected Result: rows=5 columns=['location', 'department_id', 'department_name'] sample=[{'location': 'Bangalore', 'department_id': 1, 'department_name': 'IT'}, {'location': 'Chennai', 'department_id': 3, 'department_name': 'Finance'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0194 (cold_cache, semantic, ORDER_BY)**
  - NL: `Please display employee projects sorted as specified.`
  - Expected SQL: `SELECT hours_per_week FROM employee_projects ORDER BY hours_per_week DESC LIMIT 8;`
  - Generated SQL: `SELECT * FROM employee_projects ORDER BY role AS specified;`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Invalid expression / Unexpected token. Line 1, Col: 48.\n  SELECT * FROM employee_projects ORDER BY role \x1b[4mAS\x1b[0m specified;']
  - Expected Result: rows=0 columns=['hours_per_week'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0199 (cold_cache, semantic, ORDER_BY)**
  - NL: `Please display employees sorted as specified.`
  - Expected SQL: `SELECT salary, joining_date FROM employees ORDER BY salary ASC LIMIT 9;`
  - Generated SQL: `SELECT * FROM employees ORDER BY employee_id AS specified`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Invalid expression / Unexpected token. Line 1, Col: 47.\n  SELECT * FROM employees ORDER BY employee_id \x1b[4mAS\x1b[0m specified']
  - Expected Result: rows=8 columns=['salary', 'joining_date'] sample=[{'salary': 48000, 'joining_date': '2022-04-03'}, {'salary': 54000, 'joining_date': '2023-02-06'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0204 (cold_cache, semantic, ORDER_BY)**
  - NL: `Please display products sorted as specified.`
  - Expected SQL: `SELECT price, product_id, product_name FROM products ORDER BY price DESC LIMIT 10;`
  - Generated SQL: `SELECT * FROM products ORDER BY id AS specified`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Invalid expression / Unexpected token. Line 1, Col: 37.\n  SELECT * FROM products ORDER BY id \x1b[4mAS\x1b[0m specified']
  - Expected Result: rows=2 columns=['price', 'product_id', 'product_name'] sample=[{'price': 49.99, 'product_id': 1, 'product_name': 'Analytics Pack'}, {'price': 19.99, 'product_id': 2, 'product_name': 'Cache Booster'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0214 (cold_cache, semantic, ORDER_BY)**
  - NL: `Please display query history sorted as specified.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history ORDER BY rows_returned DESC LIMIT 12;`
  - Generated SQL: `SELECT * FROM query_history ORDER BY generated_sql AS specified`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Invalid expression / Unexpected token. Line 1, Col: 53.\n  SELECT * FROM query_history ORDER BY generated_sql \x1b[4mAS\x1b[0m specified']
  - Expected Result: rows=12 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 1218, 'created_at': '2026-07-05 15:50:20.309533'}, {'rows_returned': 1218, 'created_at': '2026-07-05 15:56:19.302383'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0270 (cold_cache, semantic, LIMIT)**
  - NL: `Fetch the limited employee projects results.`
  - Expected SQL: `SELECT hours_per_week FROM employee_projects LIMIT 6 OFFSET 3;`
  - Generated SQL: `SELECT * FROM employee_projects LIMIT :fetch :limited`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Invalid expression / Unexpected token. Line 1, Col: 39.\n  SELECT * FROM employee_projects LIMIT \x1b[4m:\x1b[0mfetch :limited']
  - Expected Result: rows=0 columns=['hours_per_week'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0280 (cold_cache, semantic, LIMIT)**
  - NL: `Fetch the limited products results.`
  - Expected SQL: `SELECT price, product_id, product_name FROM products LIMIT 3 OFFSET 1;`
  - Generated SQL: `SELECT * FROM products LIMIT :fetch, :results`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Invalid expression / Unexpected token. Line 1, Col: 30.\n  SELECT * FROM products LIMIT \x1b[4m:\x1b[0mfetch, :results']
  - Expected Result: rows=1 columns=['price', 'product_id', 'product_name'] sample=[{'price': 19.99, 'product_id': 2, 'product_name': 'Cache Booster'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0285 (cold_cache, semantic, LIMIT)**
  - NL: `Fetch the limited projects results.`
  - Expected SQL: `SELECT project_id FROM projects LIMIT 4 OFFSET 2;`
  - Generated SQL: `SELECT * FROM projects LIMIT :limited results`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['SQL syntax error: Invalid expression / Unexpected token. Line 1, Col: 45.\n  SELECT * FROM projects LIMIT :limited \x1b[4mresults\x1b[0m']
  - Expected Result: rows=3 columns=['project_id'] sample=[{'project_id': 3}, {'project_id': 4}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
### EXISTS clause mismatch
- **F0286 (cold_cache, functional, EXISTS)**
  - NL: `Show books that have matching authors for existence check 1.`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 1);`
  - Generated SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Executed SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['book_id', 'title', 'author_id', 'price'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0289 (cold_cache, functional, EXISTS)**
  - NL: `Show books that have matching authors for existence check 4.`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 4);`
  - Generated SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Executed SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['book_id', 'title', 'author_id', 'price'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0292 (cold_cache, functional, EXISTS)**
  - NL: `Show books that have matching authors for existence check 7.`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 7);`
  - Generated SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Executed SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['book_id', 'title', 'author_id', 'price'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0295 (cold_cache, functional, EXISTS)**
  - NL: `Show books that have matching authors for existence check 10.`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 10);`
  - Generated SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Executed SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['book_id', 'title', 'author_id', 'price'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0298 (cold_cache, functional, EXISTS)**
  - NL: `Show books that have matching authors for existence check 13.`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 13);`
  - Generated SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Executed SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['book_id', 'title', 'author_id', 'price'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S1426 (cold_cache, semantic, EXISTS)**
  - NL: `Find authors that have matching related rows.`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 1);`
  - Generated SQL: `SELECT * FROM authors WHERE author_id IN ( SELECT author_id FROM books );`
  - Executed SQL: `SELECT * FROM authors WHERE author_id IN ( SELECT author_id FROM books );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=4 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 1, 'author_name': 'Robert Martin', 'country': 'USA'}, {'author_id': 2, 'author_name': 'Martin Fowler', 'country': 'UK'}]
  - Failure: Backend result set differs from expected SQL result.
- **S1428 (cold_cache, semantic, EXISTS)**
  - NL: `Which authors have associated data?`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 1);`
  - Generated SQL: `SELECT * FROM authors WHERE author_id IN ( SELECT employee_id FROM employees );`
  - Executed SQL: `SELECT * FROM authors WHERE author_id IN ( SELECT employee_id FROM employees );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S1429 (cold_cache, semantic, EXISTS)**
  - NL: `Please return authors with existing relationships.`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 1);`
  - Generated SQL: `SELECT * FROM authors WHERE author_id IN ( SELECT employee_id FROM employees )`
  - Executed SQL: `SELECT * FROM authors WHERE author_id IN ( SELECT employee_id FROM employees )`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S1441 (cold_cache, semantic, EXISTS)**
  - NL: `Can you show books that have matching authors for existence check 4.`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 4);`
  - Generated SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Executed SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['book_id', 'title', 'author_id', 'price'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S1442 (cold_cache, semantic, EXISTS)**
  - NL: `Please show books that have matching authors for existence check 4.`
  - Expected SQL: `SELECT * FROM books WHERE EXISTS (SELECT 1 FROM authors WHERE books.author_id = authors.author_id AND authors.author_id IS NOT NULL AND books.author_id IS NOT NULL LIMIT 4);`
  - Generated SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Executed SQL: `SELECT * FROM books WHERE author_id IN ( SELECT author_id FROM authors WHERE country LIKE 'that' ) AND price = ( SELECT price FROM products WHERE product_name = 'matching' );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['book_id', 'title', 'author_id', 'price'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
### Nested query result mismatch
- **F0197 (cold_cache, functional, NESTED)**
  - NL: `Find books selected by a nested condition with price is at least 1.`
  - Expected SQL: `SELECT * FROM books WHERE book_id IN (SELECT book_id FROM books WHERE price >= 1);`
  - Generated SQL: `SELECT book_id FROM books WHERE price >= 1 AND title IN ( SELECT title FROM books )`
  - Executed SQL: `SELECT book_id FROM books WHERE price >= 1 AND title IN ( SELECT title FROM books )`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=5 columns=['book_id'] sample=[{'book_id': 1}, {'book_id': 2}]
  - Failure: Backend result set differs from expected SQL result.
- **F0202 (cold_cache, functional, NESTED)**
  - NL: `Show projects whose keys appear in a subquery where budget is at least 6.`
  - Expected SQL: `SELECT * FROM projects WHERE project_id IN (SELECT project_id FROM projects WHERE budget >= 6);`
  - Generated SQL: `SELECT *
FROM projects
WHERE project_id IN (
    SELECT project_id
    FROM query_history
    WHERE natural_language_query LIKE '%%keys appear in subquery where budget is at least 6%'
) AND budget >= 6;`
  - Executed SQL: `SELECT *
FROM projects
WHERE project_id IN (
    SELECT project_id
    FROM query_history
    WHERE natural_language_query LIKE '%%keys appear in subquery where budget is at least 6%'
) AND budget >= 6;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['project_id', 'project_name', 'budget'] sample=[{'project_id': 1, 'project_name': 'Semantic Cache Optimization', 'budget': 125000.0}, {'project_id': 2, 'project_name': 'LLM SQL Generation', 'budget': 185000.0}]
  - Actual Result: rows=0 columns=['project_id', 'project_name', 'budget'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0203 (cold_cache, functional, NESTED)**
  - NL: `Find query history selected by a nested condition with rows returned is at least 7.`
  - Expected SQL: `SELECT * FROM query_history WHERE id IN (SELECT id FROM query_history WHERE rows_returned >= 7);`
  - Generated SQL: `SELECT * FROM query_history WHERE natural_language_query LIKE '%selected%' AND generated_sql LIKE '%WHERE %' AND rows_returned >= 7;`
  - Executed SQL: `SELECT * FROM query_history WHERE natural_language_query LIKE '%selected%' AND generated_sql LIKE '%WHERE %' AND rows_returned >= 7;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=183 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 28, 'natural_language_query': 'show all employees', 'generated_sql': 'SELECT * FROM employees;', 'generation_mode': 'LLM', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.5616, 'rows_returned': 8, 'created_at': '2026-07-01 17:13:54.870163'}, {'id': 54, 'natural_language_query': 'Show employee age', 'generated_sql': "SELECT DATE('now') - employees.joining_date AS age FROM employees", 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.6566, 'rows_returned': 8, 'created_at': '2026-07-03 17:29:46.498401'}]
  - Actual Result: rows=2 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 270, 'natural_language_query': 'Find employees selected by a nested condition with salary is at least 4.', 'generated_sql': 'SELECT * FROM employees WHERE salary >= 4', 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.4199, 'rows_returned': 8, 'created_at': '2026-07-05 15:45:20.773653'}, {'id': 2144, 'natural_language_query': 'Find employees selected by a nested condition with salary is at least 4.', 'generated_sql': 'SELECT * FROM employees WHERE salary >= 4', 'generation_mode': 'LLM', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.1089, 'rows_returned': 8, 'created_at': '2026-07-05 15:54:24.383688'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0204 (cold_cache, functional, NESTED)**
  - NL: `Return vendors using a subquery filtered for rating is at least 8.`
  - Expected SQL: `SELECT * FROM vendors WHERE id IN (SELECT id FROM vendors WHERE rating >= 8);`
  - Generated SQL: `SELECT * 
FROM vendors 
WHERE rating >= (SELECT MIN(rating) FROM vendors WHERE rating IS NOT NULL);`
  - Executed SQL: `SELECT * 
FROM vendors 
WHERE rating >= (SELECT MIN(rating) FROM vendors WHERE rating IS NOT NULL);`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['id', 'vendor_name', 'city', 'rating'] sample=[]
  - Actual Result: rows=4 columns=['id', 'vendor_name', 'city', 'rating'] sample=[{'id': 1, 'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'id': 2, 'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Failure: Backend result set differs from expected SQL result.
- **F0207 (cold_cache, functional, NESTED)**
  - NL: `Return departments using a subquery filtered for location has at least 12 characters.`
  - Expected SQL: `SELECT * FROM departments WHERE department_id IN (SELECT department_id FROM departments WHERE location IS NOT NULL AND LENGTH(location) >= 12);`
  - Generated SQL: `SELECT * FROM departments WHERE department_name IN ( SELECT department_name FROM departments WHERE LENGTH(location) >= 3 );`
  - Executed SQL: `SELECT * FROM departments WHERE department_name IN ( SELECT department_name FROM departments WHERE LENGTH(location) >= 3 );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['department_id', 'department_name', 'location'] sample=[]
  - Actual Result: rows=5 columns=['department_id', 'department_name', 'location'] sample=[{'department_id': 1, 'department_name': 'IT', 'location': 'Bangalore'}, {'department_id': 2, 'department_name': 'HR', 'location': 'Mysore'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0213 (cold_cache, functional, NESTED)**
  - NL: `Return vendors using a subquery filtered for rating is at least 17.`
  - Expected SQL: `SELECT * FROM vendors WHERE id IN (SELECT id FROM vendors WHERE rating >= 17);`
  - Generated SQL: `SELECT * 
FROM vendors 
WHERE rating >= (SELECT MIN(rating) FROM vendors WHERE rating IS NOT NULL);`
  - Executed SQL: `SELECT * 
FROM vendors 
WHERE rating >= (SELECT MIN(rating) FROM vendors WHERE rating IS NOT NULL);`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['id', 'vendor_name', 'city', 'rating'] sample=[]
  - Actual Result: rows=4 columns=['id', 'vendor_name', 'city', 'rating'] sample=[{'id': 1, 'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'id': 2, 'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Failure: Backend result set differs from expected SQL result.
- **F0216 (cold_cache, functional, NESTED)**
  - NL: `Return departments using a subquery filtered for location has at least 21 characters.`
  - Expected SQL: `SELECT * FROM departments WHERE department_id IN (SELECT department_id FROM departments WHERE location IS NOT NULL AND LENGTH(location) >= 21);`
  - Generated SQL: `SELECT * FROM departments WHERE department_name IN ( SELECT department_name FROM departments WHERE LENGTH(location) >= 3 );`
  - Executed SQL: `SELECT * FROM departments WHERE department_name IN ( SELECT department_name FROM departments WHERE LENGTH(location) >= 3 );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['department_id', 'department_name', 'location'] sample=[]
  - Actual Result: rows=5 columns=['department_id', 'department_name', 'location'] sample=[{'department_id': 1, 'department_name': 'IT', 'location': 'Bangalore'}, {'department_id': 2, 'department_name': 'HR', 'location': 'Mysore'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0219 (cold_cache, functional, NESTED)**
  - NL: `Return products using a subquery filtered for price is at least 23.`
  - Expected SQL: `SELECT * FROM products WHERE product_id IN (SELECT product_id FROM products WHERE price >= 23);`
  - Generated SQL: `SELECT * FROM products WHERE price >= ( SELECT price FROM books );`
  - Executed SQL: `SELECT * FROM products WHERE price >= ( SELECT price FROM books );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['product_id', 'product_name', 'price'] sample=[{'product_id': 1, 'product_name': 'Analytics Pack', 'price': 49.99}]
  - Actual Result: rows=0 columns=['product_id', 'product_name', 'price'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0976 (cold_cache, semantic, NESTED)**
  - NL: `Find authors using the nested condition.`
  - Expected SQL: `SELECT * FROM authors WHERE author_id IN (SELECT author_id FROM authors WHERE author_id >= 0);`
  - Generated SQL: `SELECT * FROM authors WHERE author_id IN ( SELECT author_id FROM books WHERE title = 'using' );`
  - Executed SQL: `SELECT * FROM authors WHERE author_id IN ( SELECT author_id FROM books WHERE title = 'using' );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 1, 'author_name': 'Robert Martin', 'country': 'USA'}, {'author_id': 2, 'author_name': 'Martin Fowler', 'country': 'UK'}]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0983 (cold_cache, semantic, NESTED)**
  - NL: `Which books appear in the nested result?`
  - Expected SQL: `SELECT * FROM books WHERE book_id IN (SELECT book_id FROM books WHERE price >= 1);`
  - Generated SQL: `SELECT book_id FROM books WHERE title = 'nested result'`
  - Executed SQL: `SELECT book_id FROM books WHERE title = 'nested result'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}, {'book_id': 2, 'title': 'Refactoring', 'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=0 columns=['book_id'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
### Missing aggregate function
- **F0090 (cold_cache, functional, COUNT)**
  - NL: `Count authors records where author id is at least 9.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM authors WHERE author_id >= 9;`
  - Generated SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Executed SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0097 (cold_cache, functional, COUNT)**
  - NL: `How many query history have rows returned is at least 16?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM query_history WHERE rows_returned >= 16;`
  - Generated SQL: `SELECT * FROM query_history WHERE rows_returned >= 16;`
  - Executed SQL: `SELECT * FROM query_history WHERE rows_returned >= 16;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 44}]
  - Actual Result: rows=44 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 82, 'natural_language_query': 'Display rows returned, created at from query history.', 'generated_sql': 'SELECT rows_returned, created_at FROM query_history', 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.4932, 'rows_returned': 81, 'created_at': '2026-07-05 15:44:08.168872'}, {'id': 106, 'natural_language_query': 'Show query history with execution time less than 16.', 'generated_sql': 'SELECT * FROM query_history WHERE execution_time < 16', 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.5282, 'rows_returned': 105, 'created_at': '2026-07-05 15:44:18.353280'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0420 (cold_cache, semantic, COUNT)**
  - NL: `Give me the total employee projects.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM employee_projects WHERE hours_per_week >= 3;`
  - Generated SQL: `SELECT * FROM employee_projects WHERE role = 'limited'`
  - Executed SQL: `SELECT * FROM employee_projects WHERE role = 'limited'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0440 (cold_cache, semantic, COUNT)**
  - NL: `Give me the total query history.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM query_history WHERE rows_returned >= 7;`
  - Generated SQL: `SELECT * FROM query_history`
  - Executed SQL: `SELECT * FROM query_history`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 183}]
  - Actual Result: rows=3836 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 1, 'natural_language_query': 'Show employees from Finance', 'generated_sql': "SELECT * FROM employees\nWHERE department = 'Finance';", 'generation_mode': 'Rule', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.1101, 'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'id': 2, 'natural_language_query': 'Show all vendors', 'generated_sql': 'SELECT * FROM vendors;', 'generation_mode': 'Llm', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.0345, 'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0446 (cold_cache, semantic, COUNT)**
  - NL: `Can you count authors records where author id is at least 9.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM authors WHERE author_id >= 9;`
  - Generated SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Executed SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0447 (cold_cache, semantic, COUNT)**
  - NL: `Please count authors records where author id is at least 9.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM authors WHERE author_id >= 9;`
  - Generated SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Executed SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0448 (cold_cache, semantic, COUNT)**
  - NL: `I need to count authors records where author id is at least 9.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM authors WHERE author_id >= 9;`
  - Generated SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Executed SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0449 (cold_cache, semantic, COUNT)**
  - NL: `Could you count authors records where author id is at least 9.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM authors WHERE author_id >= 9;`
  - Generated SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Executed SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0450 (cold_cache, semantic, COUNT)**
  - NL: `Return the authors results for this request: count authors records where author id is at least 9.`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM authors WHERE author_id >= 9;`
  - Generated SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Executed SQL: `SELECT * FROM authors WHERE author_id >= 9`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0455 (cold_cache, semantic, COUNT)**
  - NL: `Return the books results for this request: how many books have author id is at least 10?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM books WHERE author_id >= 10;`
  - Generated SQL: `SELECT * FROM books WHERE author_id >= 10;`
  - Executed SQL: `SELECT * FROM books WHERE author_id >= 10;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 0}]
  - Actual Result: rows=0 columns=['book_id', 'title', 'author_id', 'price'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
### IN clause mismatch
- **F0275 (cold_cache, functional, IN)**
  - NL: `Find employees selected by an IN query with salary is at least 4.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 4 GROUP BY employee_id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Executed SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=0 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0277 (cold_cache, functional, IN)**
  - NL: `Show projects whose project id is in a subquery where budget is at least 6.`
  - Expected SQL: `SELECT * FROM projects WHERE project_id IN (SELECT project_id FROM projects WHERE budget >= 6 GROUP BY project_id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT *
FROM projects
WHERE project_id IN (
    SELECT project_id
    FROM query_history
    WHERE natural_language_query LIKE '%%keys appear in subquery where budget is at least 6%'
) AND budget >= 6;`
  - Executed SQL: `SELECT *
FROM projects
WHERE project_id IN (
    SELECT project_id
    FROM query_history
    WHERE natural_language_query LIKE '%%keys appear in subquery where budget is at least 6%'
) AND budget >= 6;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['project_id', 'project_name', 'budget'] sample=[{'project_id': 1, 'project_name': 'Semantic Cache Optimization', 'budget': 125000.0}, {'project_id': 2, 'project_name': 'LLM SQL Generation', 'budget': 185000.0}]
  - Actual Result: rows=0 columns=['project_id', 'project_name', 'budget'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **F0278 (cold_cache, functional, IN)**
  - NL: `Find query history selected by an IN query with rows returned is at least 7.`
  - Expected SQL: `SELECT * FROM query_history WHERE id IN (SELECT id FROM query_history WHERE rows_returned >= 7 GROUP BY id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT * FROM query_history WHERE natural_language_query LIKE '%selected%' AND generated_sql LIKE '%WHERE %' AND rows_returned >= 7;`
  - Executed SQL: `SELECT * FROM query_history WHERE natural_language_query LIKE '%selected%' AND generated_sql LIKE '%WHERE %' AND rows_returned >= 7;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=183 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 28, 'natural_language_query': 'show all employees', 'generated_sql': 'SELECT * FROM employees;', 'generation_mode': 'LLM', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.5616, 'rows_returned': 8, 'created_at': '2026-07-01 17:13:54.870163'}, {'id': 54, 'natural_language_query': 'Show employee age', 'generated_sql': "SELECT DATE('now') - employees.joining_date AS age FROM employees", 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.6566, 'rows_returned': 8, 'created_at': '2026-07-03 17:29:46.498401'}]
  - Actual Result: rows=2 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 270, 'natural_language_query': 'Find employees selected by a nested condition with salary is at least 4.', 'generated_sql': 'SELECT * FROM employees WHERE salary >= 4', 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.4199, 'rows_returned': 8, 'created_at': '2026-07-05 15:45:20.773653'}, {'id': 2144, 'natural_language_query': 'Find employees selected by a nested condition with salary is at least 4.', 'generated_sql': 'SELECT * FROM employees WHERE salary >= 4', 'generation_mode': 'LLM', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.1089, 'rows_returned': 8, 'created_at': '2026-07-05 15:54:24.383688'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0282 (cold_cache, functional, IN)**
  - NL: `Return departments where department id appears in the grouped inner result for location has at least 12 characters.`
  - Expected SQL: `SELECT * FROM departments WHERE department_id IN (SELECT department_id FROM departments WHERE location IS NOT NULL AND LENGTH(location) >= 12 GROUP BY department_id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT *
FROM departments
WHERE department_id IN (
  SELECT department_id 
  FROM departments 
  GROUP BY department_id 
  HAVING LENGTH(location) >= 3
);`
  - Executed SQL: `SELECT *
FROM departments
WHERE department_id IN (
  SELECT department_id 
  FROM departments 
  GROUP BY department_id 
  HAVING LENGTH(location) >= 3
);`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['department_id', 'department_name', 'location'] sample=[]
  - Actual Result: rows=5 columns=['department_id', 'department_name', 'location'] sample=[{'department_id': 1, 'department_name': 'IT', 'location': 'Bangalore'}, {'department_id': 2, 'department_name': 'HR', 'location': 'Mysore'}]
  - Failure: Backend result set differs from expected SQL result.
- **F0284 (cold_cache, functional, IN)**
  - NL: `Find employees selected by an IN query with salary is at least 13.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 13 GROUP BY employee_id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 13`
  - Executed SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 13`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=0 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S1371 (cold_cache, semantic, IN)**
  - NL: `Can you find employees selected by an IN query with salary is at least 4.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 4 GROUP BY employee_id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Executed SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=0 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S1372 (cold_cache, semantic, IN)**
  - NL: `Please find employees selected by an IN query with salary is at least 4.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 4 GROUP BY employee_id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Executed SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=0 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S1373 (cold_cache, semantic, IN)**
  - NL: `I need to find employees selected by an IN query with salary is at least 4.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 4 GROUP BY employee_id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Executed SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=0 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S1374 (cold_cache, semantic, IN)**
  - NL: `Could you find employees selected by an IN query with salary is at least 4.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 4 GROUP BY employee_id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Executed SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=0 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S1375 (cold_cache, semantic, IN)**
  - NL: `Return the employees results for this request: find employees selected by an IN query with salary is at least 4.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 4 GROUP BY employee_id HAVING COUNT(*) >= 1);`
  - Generated SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Executed SQL: `SELECT * FROM employees WHERE department = 'selected' AND salary >= 4;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=0 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
### HAVING clause mismatch
- **F0251 (cold_cache, functional, HAVING)**
  - NL: `Show authors groups by author name with more than 0 records.`
  - Expected SQL: `SELECT author_name, COUNT(*) AS row_count FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1 GROUP BY author_name HAVING COUNT(*) > 0 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT author_id FROM authors GROUP BY author_name HAVING COUNT(*) > 0`
  - Executed SQL: `SELECT author_id FROM authors GROUP BY author_name HAVING COUNT(*) > 0`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_name', 'row_count'] sample=[{'author_name': 'Robert Martin', 'row_count': 1}, {'author_name': 'Martin Fowler', 'row_count': 1}]
  - Actual Result: rows=4 columns=['author_id'] sample=[{'author_id': 3}, {'author_id': 4}]
  - Failure: Backend result set differs from expected SQL result.
- **F0252 (cold_cache, functional, HAVING)**
  - NL: `List title groups in books whose counts exceed 1.`
  - Expected SQL: `SELECT title, COUNT(*) AS row_count FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 2 GROUP BY title HAVING COUNT(*) > 1 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT book_id 
FROM books WHERE price > '1'`
  - Executed SQL: `SELECT book_id 
FROM books WHERE price > '1'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['title', 'row_count'] sample=[]
  - Actual Result: rows=5 columns=['book_id'] sample=[{'book_id': 1}, {'book_id': 2}]
  - Failure: Backend result set differs from expected SQL result.
- **F0270 (cold_cache, functional, HAVING)**
  - NL: `List title groups in books whose counts exceed 19.`
  - Expected SQL: `SELECT title, COUNT(*) AS row_count FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 20 GROUP BY title HAVING COUNT(*) > 19 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT title FROM books WHERE price * (SELECT COUNT(*) FROM employees) > 19`
  - Executed SQL: `SELECT title FROM books WHERE price * (SELECT COUNT(*) FROM employees) > 19`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['title', 'row_count'] sample=[]
  - Actual Result: rows=5 columns=['title'] sample=[{'title': 'Clean Code'}, {'title': 'Refactoring'}]
  - Failure: Backend result set differs from expected SQL result.
- **S1254 (cold_cache, semantic, HAVING)**
  - NL: `Please return qualifying grouped authors.`
  - Expected SQL: `SELECT author_name, COUNT(*) AS row_count FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1 GROUP BY author_name HAVING COUNT(*) > 0 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT * FROM authors GROUP BY author_name`
  - Executed SQL: `SELECT * FROM authors GROUP BY author_name`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['author_name', 'row_count'] sample=[{'author_name': 'Robert Martin', 'row_count': 1}, {'author_name': 'Martin Fowler', 'row_count': 1}]
  - Actual Result: rows=4 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 3, 'author_name': 'Andrew Tanenbaum', 'country': 'Netherlands'}, {'author_id': 4, 'author_name': 'Ian Goodfellow', 'country': 'USA'}]
  - Failure: Backend result set differs from expected SQL result.
- **S1259 (cold_cache, semantic, HAVING)**
  - NL: `Please return qualifying grouped books.`
  - Expected SQL: `SELECT title, COUNT(*) AS row_count FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 2 GROUP BY title HAVING COUNT(*) > 1 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT book_id FROM books GROUP BY title`
  - Executed SQL: `SELECT book_id FROM books GROUP BY title`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['title', 'row_count'] sample=[]
  - Actual Result: rows=5 columns=['book_id'] sample=[{'book_id': 5}, {'book_id': 1}]
  - Failure: Backend result set differs from expected SQL result.
- **S1260 (cold_cache, semantic, HAVING)**
  - NL: `List grouped books after applying the aggregate threshold.`
  - Expected SQL: `SELECT title, COUNT(*) AS row_count FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 2 GROUP BY title HAVING COUNT(*) > 1 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT * FROM books GROUP BY title HAVING MAX(price) > 20`
  - Executed SQL: `SELECT * FROM books GROUP BY title HAVING MAX(price) > 20`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['title', 'row_count'] sample=[]
  - Actual Result: rows=5 columns=['book_id', 'title', 'author_id', 'price'] sample=[{'book_id': 5, 'title': 'Clean Architecture', 'author_id': 1, 'price': 700.0}, {'book_id': 1, 'title': 'Clean Code', 'author_id': 1, 'price': 650.0}]
  - Failure: Backend result set differs from expected SQL result.
- **S1274 (cold_cache, semantic, HAVING)**
  - NL: `Please return qualifying grouped employees.`
  - Expected SQL: `SELECT email, COUNT(*) AS row_count FROM employees WHERE email IS NOT NULL AND LENGTH(email) >= 5 GROUP BY email HAVING COUNT(*) > 4 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT DISTINCT department FROM employees GROUP BY department`
  - Executed SQL: `SELECT DISTINCT department FROM employees GROUP BY department`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['email', 'row_count'] sample=[]
  - Actual Result: rows=4 columns=['department'] sample=[{'department': 'Engineering'}, {'department': 'Finance'}]
  - Failure: Backend result set differs from expected SQL result.
- **S1277 (cold_cache, semantic, HAVING)**
  - NL: `Show products groups that pass the aggregate filter.`
  - Expected SQL: `SELECT product_name, COUNT(*) AS row_count FROM products WHERE product_name IS NOT NULL AND LENGTH(product_name) >= 6 GROUP BY product_name HAVING COUNT(*) > 5 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT * FROM products WHERE product_id IN ( SELECT id FROM vendors GROUP BY vendor_name HAVING SUM(rating) > 3 );`
  - Executed SQL: `SELECT * FROM products WHERE product_id IN ( SELECT id FROM vendors GROUP BY vendor_name HAVING SUM(rating) > 3 );`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['product_name', 'row_count'] sample=[]
  - Actual Result: rows=2 columns=['product_id', 'product_name', 'price'] sample=[{'product_id': 1, 'product_name': 'Analytics Pack', 'price': 49.99}, {'product_id': 2, 'product_name': 'Cache Booster', 'price': 19.99}]
  - Failure: Backend result set differs from expected SQL result.
- **S1280 (cold_cache, semantic, HAVING)**
  - NL: `List grouped products after applying the aggregate threshold.`
  - Expected SQL: `SELECT product_name, COUNT(*) AS row_count FROM products WHERE product_name IS NOT NULL AND LENGTH(product_name) >= 6 GROUP BY product_name HAVING COUNT(*) > 5 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT * FROM products WHERE price >= ( SELECT AVG(price) FROM products )`
  - Executed SQL: `SELECT * FROM products WHERE price >= ( SELECT AVG(price) FROM products )`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['product_name', 'row_count'] sample=[]
  - Actual Result: rows=1 columns=['product_id', 'product_name', 'price'] sample=[{'product_id': 1, 'product_name': 'Analytics Pack', 'price': 49.99}]
  - Failure: Backend result set differs from expected SQL result.
- **S1287 (cold_cache, semantic, HAVING)**
  - NL: `Show query history groups that pass the aggregate filter.`
  - Expected SQL: `SELECT generation_mode, COUNT(*) AS row_count FROM query_history WHERE generation_mode IS NOT NULL AND LENGTH(generation_mode) >= 8 GROUP BY generation_mode HAVING COUNT(*) > 7 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT * FROM query_history WHERE natural_language_query LIKE '%groups%' AND natural_language_query LIKE '%pass%' AND natural_language_query LIKE '%aggregate%' AND natural_language_query LIKE '%filter%';`
  - Executed SQL: `SELECT * FROM query_history WHERE natural_language_query LIKE '%groups%' AND natural_language_query LIKE '%pass%' AND natural_language_query LIKE '%aggregate%' AND natural_language_query LIKE '%filter%';`
  - Validation: `valid` errors=[]
  - Expected Result: rows=0 columns=['generation_mode', 'row_count'] sample=[]
  - Actual Result: rows=15 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 1608, 'natural_language_query': 'Show books groups that pass the aggregate filter.', 'generated_sql': 'SELECT * FROM books WHERE title LIKE "%groups%" AND price > ( SELECT AVG(price) FROM books );', 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Invalid', 'execution_time': 0.7569, 'rows_returned': 0, 'created_at': '2026-07-05 15:52:03.154141'}, {'id': 1613, 'natural_language_query': 'Show departments groups that pass the aggregate filter.', 'generated_sql': "SELECT * FROM departments WHERE departments.department_name LIKE '%groups%' AND departments.location LIKE '%filter%'", 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.7185, 'rows_returned': 0, 'created_at': '2026-07-05 15:52:06.188587'}]
  - Failure: Backend result set differs from expected SQL result.
### Invalid query repaired into valid SQL
- **I0001 (cold_cache, invalid, None)**
  - NL: `Show records from the missing authors archive 0`
  - Expected SQL: `SELECT * FROM missing_authors_0;`
  - Generated SQL: `SELECT * FROM authors WHERE author_id = 0`
  - Executed SQL: `SELECT * FROM authors WHERE author_id = 0`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0002 (cold_cache, invalid, None)**
  - NL: `Show the missing column 1 for books`
  - Expected SQL: `SELECT missing_column_1 FROM books;`
  - Generated SQL: `SELECT book_id FROM books WHERE book_id = 'missing'`
  - Executed SQL: `SELECT book_id FROM books WHERE book_id = 'missing'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['book_id'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0003 (cold_cache, invalid, None)**
  - NL: `Run malformed select request 2 for departments`
  - Expected SQL: `SELECT * FROM departments WHERE ;`
  - Generated SQL: `SELECT * FROM departments WHERE department_id = 'request'`
  - Executed SQL: `SELECT * FROM departments WHERE department_id = 'request'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['department_id', 'department_name', 'location'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0007 (cold_cache, invalid, None)**
  - NL: `Run malformed select request 6 for projects`
  - Expected SQL: `SELECT * FROM projects WHERE ;`
  - Generated SQL: `SELECT * FROM "projects"`
  - Executed SQL: `SELECT * FROM "projects"`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=5 columns=['project_id', 'project_name', 'budget'] sample=[{'project_id': 1, 'project_name': 'Semantic Cache Optimization', 'budget': 125000.0}, {'project_id': 2, 'project_name': 'LLM SQL Generation', 'budget': 185000.0}]
  - Failure: Invalid benchmark query was not rejected.
- **I0009 (cold_cache, invalid, None)**
  - NL: `Show records from the missing vendors archive 8`
  - Expected SQL: `SELECT * FROM missing_vendors_8;`
  - Generated SQL: `SELECT * FROM vendors WHERE id = 'archive' AND vendor_name = 'missing' LIMIT 8;`
  - Executed SQL: `SELECT * FROM vendors WHERE id = 'archive' AND vendor_name = 'missing' LIMIT 8;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['id', 'vendor_name', 'city', 'rating'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0013 (cold_cache, invalid, None)**
  - NL: `Show records from the missing employee_projects archive 12`
  - Expected SQL: `SELECT * FROM missing_employee_projects_12;`
  - Generated SQL: `SELECT * FROM employee_projects WHERE role = 'archive' AND hours_per_week = 12;`
  - Executed SQL: `SELECT * FROM employee_projects WHERE role = 'archive' AND hours_per_week = 12;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0017 (cold_cache, invalid, None)**
  - NL: `Show records from the missing query_history archive 16`
  - Expected SQL: `SELECT * FROM missing_query_history_16;`
  - Generated SQL: `SELECT * FROM query_history WHERE natural_language_query = 'missing' AND generated_sql IS NULL AND execution_time > 16`
  - Executed SQL: `SELECT * FROM query_history WHERE natural_language_query = 'missing' AND generated_sql IS NULL AND execution_time > 16`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0018 (cold_cache, invalid, None)**
  - NL: `Show the missing column 17 for vendors`
  - Expected SQL: `SELECT missing_column_17 FROM vendors;`
  - Generated SQL: `SELECT id FROM vendors WHERE city = 'missing' AND vendor_name = 'column' LIMIT 1;`
  - Executed SQL: `SELECT id FROM vendors WHERE city = 'missing' AND vendor_name = 'column' LIMIT 1;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['id'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0019 (cold_cache, invalid, None)**
  - NL: `Run malformed select request 18 for authors`
  - Expected SQL: `SELECT * FROM authors WHERE ;`
  - Generated SQL: `SELECT * FROM authors WHERE author_id = 18`
  - Executed SQL: `SELECT * FROM authors WHERE author_id = 18`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['author_id', 'author_name', 'country'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
- **I0021 (cold_cache, invalid, None)**
  - NL: `Show records from the missing departments archive 20`
  - Expected SQL: `SELECT * FROM missing_departments_20;`
  - Generated SQL: `SELECT * FROM departments WHERE department_id = 'archive' AND department_name = 'missing' LIMIT 20;`
  - Executed SQL: `SELECT * FROM departments WHERE department_id = 'archive' AND department_name = 'missing' LIMIT 20;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=None columns=[] sample=[]
  - Actual Result: rows=0 columns=['department_id', 'department_name', 'location'] sample=[]
  - Failure: Invalid benchmark query was not rejected.
### Backend exception / HTTP failure
- **F0135 (cold_cache, functional, MIN)**
  - NL: `Calculate the lowest price for books where title has at least 10 characters.`
  - Expected SQL: `SELECT MIN(price) AS min_price FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 10;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=1 columns=['min_price'] sample=[{'min_price': 650.0}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
- **F0150 (cold_cache, functional, MAX)**
  - NL: `Calculate the highest price for books where title has at least 10 characters.`
  - Expected SQL: `SELECT MAX(price) AS max_price FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 10;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=1 columns=['max_price'] sample=[{'max_price': 1200.0}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
- **F0175 (cold_cache, functional, GROUP_BY)**
  - NL: `Count employees for each email after filtering for email has at least 5 characters.`
  - Expected SQL: `SELECT email, COUNT(*) AS row_count FROM employees WHERE email IS NOT NULL AND LENGTH(email) >= 5 GROUP BY email ORDER BY COUNT(*) DESC;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=8 columns=['email', 'row_count'] sample=[{'email': 'ava.thompson@company.com', 'row_count': 1}, {'email': 'daniel.martinez@company.com', 'row_count': 1}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
- **F0243 (cold_cache, functional, JOIN)**
  - NL: `List 32 matching employee projects and employees records.`
  - Expected SQL: `SELECT employee_projects.*, employees.employee_id FROM employee_projects JOIN employees ON employee_projects.employee_id = employees.employee_id WHERE EXISTS (SELECT 1 FROM employees WHERE employee_projects.employee_id = employees.employee_id AND employees.employee_id IS NOT NULL) ORDER BY employee_projects.employee_id ASC LIMIT 32;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week', 'employee_id'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
- **F0255 (cold_cache, functional, HAVING)**
  - NL: `List email groups in employees whose counts exceed 4.`
  - Expected SQL: `SELECT email, COUNT(*) AS row_count FROM employees WHERE email IS NOT NULL AND LENGTH(email) >= 5 GROUP BY email HAVING COUNT(*) > 4 ORDER BY COUNT(*) DESC;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=0 columns=['email', 'row_count'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
- **F0261 (cold_cache, functional, HAVING)**
  - NL: `List title groups in books whose counts exceed 10.`
  - Expected SQL: `SELECT title, COUNT(*) AS row_count FROM books WHERE title IS NOT NULL AND LENGTH(title) >= 11 GROUP BY title HAVING COUNT(*) > 10 ORDER BY COUNT(*) DESC;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=0 columns=['title', 'row_count'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
- **F0264 (cold_cache, functional, HAVING)**
  - NL: `List email groups in employees whose counts exceed 13.`
  - Expected SQL: `SELECT email, COUNT(*) AS row_count FROM employees WHERE email IS NOT NULL AND LENGTH(email) >= 14 GROUP BY email HAVING COUNT(*) > 13 ORDER BY COUNT(*) DESC;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=0 columns=['email', 'row_count'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
- **S0371 (cold_cache, semantic, DISTINCT)**
  - NL: `List the unique country for authors.`
  - Expected SQL: `SELECT DISTINCT country FROM authors WHERE country IS NOT NULL AND LENGTH(country) >= 10 ORDER BY country ASC;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=1 columns=['country'] sample=[{'country': 'Netherlands'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
- **S0995 (cold_cache, semantic, NESTED)**
  - NL: `List employee projects whose keys are returned by the subquery.`
  - Expected SQL: `SELECT * FROM employee_projects WHERE project_id IN (SELECT project_id FROM employee_projects WHERE hours_per_week >= 3);`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
- **S1004 (cold_cache, semantic, NESTED)**
  - NL: `Please return products from the inner-query match.`
  - Expected SQL: `SELECT * FROM products WHERE product_id IN (SELECT product_id FROM products WHERE price >= 5);`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=2 columns=['product_id', 'product_name', 'price'] sample=[{'product_id': 1, 'product_name': 'Analytics Pack', 'price': 49.99}, {'product_id': 2, 'product_name': 'Cache Booster', 'price': 19.99}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 503.
### Invented non-schema column: stored
- **F0004 (cold_cache, functional, SELECT)**
  - NL: `Which hours per week from employee projects are stored?`
  - Expected SQL: `SELECT hours_per_week FROM employee_projects;`
  - Generated SQL: `SELECT role FROM employee_projects WHERE stored = 'stored'`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'employee_projects'"]
  - Expected Result: rows=0 columns=['hours_per_week'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0009 (cold_cache, functional, SELECT)**
  - NL: `Which id, vendor name, city from vendors are stored?`
  - Expected SQL: `SELECT id, vendor_name, city FROM vendors;`
  - Generated SQL: `SELECT id, vendor_name, city FROM vendors WHERE stored = 1`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'vendors'"]
  - Expected Result: rows=4 columns=['id', 'vendor_name', 'city'] sample=[{'id': 1, 'vendor_name': 'ABC Traders', 'city': 'Bangalore'}, {'id': 2, 'vendor_name': 'Global Supplies', 'city': 'Chennai'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **F0012 (cold_cache, functional, SELECT)**
  - NL: `Which name, email from employees are stored?`
  - Expected SQL: `SELECT name, email FROM employees;`
  - Generated SQL: `SELECT name, email FROM employees WHERE stored = 1;`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'employees'"]
  - Expected Result: rows=8 columns=['name', 'email'] sample=[{'name': 'David Wilson', 'email': 'david.wilson@company.com'}, {'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0018 (cold_cache, semantic, SELECT)**
  - NL: `Which hours per week for employee projects are stored?`
  - Expected SQL: `SELECT hours_per_week FROM employee_projects;`
  - Generated SQL: `SELECT role FROM employee_projects WHERE stored = 'stored'`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'employee_projects'"]
  - Expected Result: rows=0 columns=['hours_per_week'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0033 (cold_cache, semantic, SELECT)**
  - NL: `Which project id for projects are stored?`
  - Expected SQL: `SELECT project_id FROM projects;`
  - Generated SQL: `SELECT project_id FROM projects WHERE projects.stored = 't'`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'projects'"]
  - Expected Result: rows=5 columns=['project_id'] sample=[{'project_id': 1}, {'project_id': 2}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0043 (cold_cache, semantic, SELECT)**
  - NL: `Which city, id, vendor name for vendors are stored?`
  - Expected SQL: `SELECT id, vendor_name, city FROM vendors;`
  - Generated SQL: `SELECT id, vendor_name, city FROM vendors WHERE stored = 1`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'vendors'"]
  - Expected Result: rows=4 columns=['id', 'vendor_name', 'city'] sample=[{'id': 1, 'vendor_name': 'ABC Traders', 'city': 'Bangalore'}, {'id': 2, 'vendor_name': 'Global Supplies', 'city': 'Chennai'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0048 (cold_cache, semantic, SELECT)**
  - NL: `Which author id, price for books are stored?`
  - Expected SQL: `SELECT author_id, price FROM books;`
  - Generated SQL: `SELECT author_id, price FROM books WHERE stored`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'books'"]
  - Expected Result: rows=5 columns=['author_id', 'price'] sample=[{'author_id': 1, 'price': 650.0}, {'author_id': 2, 'price': 720.0}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0058 (cold_cache, semantic, SELECT)**
  - NL: `Which email, name for employees are stored?`
  - Expected SQL: `SELECT name, email FROM employees;`
  - Generated SQL: `SELECT name, email FROM employees WHERE stored = 1;`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'employees'"]
  - Expected Result: rows=8 columns=['name', 'email'] sample=[{'name': 'David Wilson', 'email': 'david.wilson@company.com'}, {'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0063 (cold_cache, semantic, SELECT)**
  - NL: `Which city, rating, vendor name for vendors are stored?`
  - Expected SQL: `SELECT vendor_name, city, rating FROM vendors;`
  - Generated SQL: `SELECT city, rating, vendor_name FROM vendors WHERE stored = 1`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'vendors'"]
  - Expected Result: rows=4 columns=['vendor_name', 'city', 'rating'] sample=[{'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0068 (cold_cache, semantic, SELECT)**
  - NL: `Which book id, price for books are stored?`
  - Expected SQL: `SELECT price, book_id FROM books;`
  - Generated SQL: `SELECT author_id, price FROM books WHERE stored`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Column 'stored' does not exist in table 'books'"]
  - Expected Result: rows=5 columns=['price', 'book_id'] sample=[{'price': 650.0, 'book_id': 1}, {'price': 720.0, 'book_id': 2}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
### Wrong or invented table
- **S0275 (cold_cache, semantic, LIMIT)**
  - NL: `Fetch the limited employees results.`
  - Expected SQL: `SELECT salary, joining_date FROM employees LIMIT 7 OFFSET 0;`
  - Generated SQL: `SELECT * FROM employees LIMIT  fetch , results`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'results' does not exist"]
  - Expected Result: rows=7 columns=['salary', 'joining_date'] sample=[{'salary': 75000, 'joining_date': '2019-07-18'}, {'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0980 (cold_cache, semantic, NESTED)**
  - NL: `List authors whose keys are returned by the subquery.`
  - Expected SQL: `SELECT * FROM authors WHERE author_id IN (SELECT author_id FROM authors WHERE author_id >= 0);`
  - Generated SQL: `SELECT * FROM authors WHERE author_id IN (SELECT keys FROM subquery)`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'subquery' does not exist"]
  - Expected Result: rows=4 columns=['author_id', 'author_name', 'country'] sample=[{'author_id': 1, 'author_name': 'Robert Martin', 'country': 'USA'}, {'author_id': 2, 'author_name': 'Martin Fowler', 'country': 'UK'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0987 (cold_cache, semantic, NESTED)**
  - NL: `Show departments selected by the subquery.`
  - Expected SQL: `SELECT * FROM departments WHERE department_id IN (SELECT department_id FROM departments WHERE location IS NOT NULL AND LENGTH(location) >= 3);`
  - Generated SQL: `SELECT * FROM departments WHERE department_id IN ( SELECT department_id FROM subquery );`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'subquery' does not exist"]
  - Expected Result: rows=5 columns=['department_id', 'department_name', 'location'] sample=[{'department_id': 1, 'department_name': 'IT', 'location': 'Bangalore'}, {'department_id': 2, 'department_name': 'HR', 'location': 'Mysore'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S1000 (cold_cache, semantic, NESTED)**
  - NL: `List employees whose keys are returned by the subquery.`
  - Expected SQL: `SELECT * FROM employees WHERE employee_id IN (SELECT employee_id FROM employees WHERE salary >= 4);`
  - Generated SQL: `SELECT * FROM employees WHERE employee_id IN ( SELECT keys FROM subquery )`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'subquery' does not exist"]
  - Expected Result: rows=8 columns=['employee_id', 'name', 'email', 'department', 'salary', 'joining_date'] sample=[{'employee_id': 101, 'name': 'David Wilson', 'email': 'david.wilson@company.com', 'department': 'Engineering', 'salary': 75000, 'joining_date': '2019-07-18'}, {'employee_id': 104, 'name': 'Sarah Johnson', 'email': 'sarah.johnson@company.com', 'department': 'Finance', 'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S1005 (cold_cache, semantic, NESTED)**
  - NL: `List products whose keys are returned by the subquery.`
  - Expected SQL: `SELECT * FROM products WHERE product_id IN (SELECT product_id FROM products WHERE price >= 5);`
  - Generated SQL: `SELECT * FROM products WHERE id IN ( SELECT keys FROM subquery )`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'subquery' does not exist"]
  - Expected Result: rows=2 columns=['product_id', 'product_name', 'price'] sample=[{'product_id': 1, 'product_name': 'Analytics Pack', 'price': 49.99}, {'product_id': 2, 'product_name': 'Cache Booster', 'price': 19.99}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S1010 (cold_cache, semantic, NESTED)**
  - NL: `List projects whose keys are returned by the subquery.`
  - Expected SQL: `SELECT * FROM projects WHERE project_id IN (SELECT project_id FROM projects WHERE budget >= 6);`
  - Generated SQL: `SELECT * FROM projects WHERE keys IN (SELECT id FROM project_keys)`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'project_keys' does not exist"]
  - Expected Result: rows=5 columns=['project_id', 'project_name', 'budget'] sample=[{'project_id': 1, 'project_name': 'Semantic Cache Optimization', 'budget': 125000.0}, {'project_id': 2, 'project_name': 'LLM SQL Generation', 'budget': 185000.0}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S1012 (cold_cache, semantic, NESTED)**
  - NL: `Show query history selected by the subquery.`
  - Expected SQL: `SELECT * FROM query_history WHERE id IN (SELECT id FROM query_history WHERE rows_returned >= 7);`
  - Generated SQL: `SELECT * FROM query_history WHERE id IN ( SELECT subquery FROM history );`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'history' does not exist"]
  - Expected Result: rows=183 columns=['id', 'natural_language_query', 'generated_sql', 'generation_mode', 'cache_status', 'validation_status', 'execution_time', 'rows_returned', 'created_at'] sample=[{'id': 28, 'natural_language_query': 'show all employees', 'generated_sql': 'SELECT * FROM employees;', 'generation_mode': 'LLM', 'cache_status': 'Hit', 'validation_status': 'Valid', 'execution_time': 0.5616, 'rows_returned': 8, 'created_at': '2026-07-01 17:13:54.870163'}, {'id': 54, 'natural_language_query': 'Show employee age', 'generated_sql': "SELECT DATE('now') - employees.joining_date AS age FROM employees", 'generation_mode': 'LLM', 'cache_status': 'Miss', 'validation_status': 'Valid', 'execution_time': 0.6566, 'rows_returned': 8, 'created_at': '2026-07-03 17:29:46.498401'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S1020 (cold_cache, semantic, NESTED)**
  - NL: `List vendors whose keys are returned by the subquery.`
  - Expected SQL: `SELECT * FROM vendors WHERE id IN (SELECT id FROM vendors WHERE rating >= 8);`
  - Generated SQL: `SELECT * FROM vendors WHERE id IN (SELECT keys FROM subquery);`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'subquery' does not exist"]
  - Expected Result: rows=0 columns=['id', 'vendor_name', 'city', 'rating'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S1291 (cold_cache, semantic, HAVING)**
  - NL: `Find grouped vendors where the group count is high enough.`
  - Expected SQL: `SELECT vendor_name, COUNT(*) AS row_count FROM vendors WHERE vendor_name IS NOT NULL AND LENGTH(vendor_name) >= 9 GROUP BY vendor_name HAVING COUNT(*) > 8 ORDER BY COUNT(*) DESC;`
  - Generated SQL: `SELECT * FROM vendors WHERE id IN ( SELECT vendor_id FROM grouped )`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'grouped' does not exist"]
  - Expected Result: rows=0 columns=['vendor_name', 'row_count'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S0275 (warm_cache, semantic, LIMIT)**
  - NL: `Fetch the limited employees results.`
  - Expected SQL: `SELECT salary, joining_date FROM employees LIMIT 7 OFFSET 0;`
  - Generated SQL: `SELECT * FROM employees LIMIT  fetch , results`
  - Executed SQL: `None`
  - Validation: `invalid` errors=["Table 'results' does not exist"]
  - Expected Result: rows=7 columns=['salary', 'joining_date'] sample=[{'salary': 75000, 'joining_date': '2019-07-18'}, {'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
### Projection mismatch
- **F0013 (cold_cache, functional, SELECT)**
  - NL: `Display vendor name, city, rating from vendors.`
  - Expected SQL: `SELECT vendor_name, city, rating FROM vendors;`
  - Generated SQL: `SELECT id, vendor_name, city, rating FROM vendors;`
  - Executed SQL: `SELECT id, vendor_name, city, rating FROM vendors;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['vendor_name', 'city', 'rating'] sample=[{'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Actual Result: rows=4 columns=['id', 'vendor_name', 'city', 'rating'] sample=[{'id': 1, 'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'id': 2, 'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Failure: Backend result set differs from expected SQL result.
- **S0008 (cold_cache, semantic, SELECT)**
  - NL: `Which author id, title for books are stored?`
  - Expected SQL: `SELECT title, author_id FROM books;`
  - Generated SQL: `SELECT T2.author_id, T1.title FROM books AS T1 INNER JOIN authors AS T2 ON T2.author_name = 'stored'`
  - Executed SQL: `SELECT T2.author_id, T1.title FROM books AS T1 INNER JOIN authors AS T2 ON T2.author_name = 'stored'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['title', 'author_id'] sample=[{'title': 'Clean Code', 'author_id': 1}, {'title': 'Refactoring', 'author_id': 2}]
  - Actual Result: rows=0 columns=['author_id', 'title'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0009 (cold_cache, semantic, SELECT)**
  - NL: `Please show author id, title for books.`
  - Expected SQL: `SELECT title, author_id FROM books;`
  - Generated SQL: `SELECT book_id, title FROM books WHERE author_id IN ( SELECT author_id FROM authors )`
  - Executed SQL: `SELECT book_id, title FROM books WHERE author_id IN ( SELECT author_id FROM authors )`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['title', 'author_id'] sample=[{'title': 'Clean Code', 'author_id': 1}, {'title': 'Refactoring', 'author_id': 2}]
  - Actual Result: rows=5 columns=['book_id', 'title'] sample=[{'book_id': 1, 'title': 'Clean Code'}, {'book_id': 2, 'title': 'Refactoring'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0023 (cold_cache, semantic, SELECT)**
  - NL: `Which joining date, salary for employees are stored?`
  - Expected SQL: `SELECT salary, joining_date FROM employees;`
  - Generated SQL: `SELECT employees.joining_date, employees.salary FROM employees WHERE employees.department = 'stored'`
  - Executed SQL: `SELECT employees.joining_date, employees.salary FROM employees WHERE employees.department = 'stored'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=8 columns=['salary', 'joining_date'] sample=[{'salary': 75000, 'joining_date': '2019-07-18'}, {'salary': 88000, 'joining_date': '2020-03-22'}]
  - Actual Result: rows=0 columns=['joining_date', 'salary'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0039 (cold_cache, semantic, SELECT)**
  - NL: `Please show created at, rows returned for query history.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history;`
  - Generated SQL: `SELECT id, created_at, rows_returned FROM query_history`
  - Executed SQL: `SELECT id, created_at, rows_returned FROM query_history`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Actual Result: rows=3836 columns=['id', 'created_at', 'rows_returned'] sample=[{'id': 1, 'created_at': '2026-06-08 13:46:02.803748', 'rows_returned': 3}, {'id': 2, 'created_at': '2026-06-08 13:46:02.842987', 'rows_returned': 4}]
  - Failure: Backend result set differs from expected SQL result.
- **S0040 (cold_cache, semantic, SELECT)**
  - NL: `Return created at, rows returned for query history.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history;`
  - Generated SQL: `SELECT id, created_at, rows_returned FROM query_history`
  - Executed SQL: `SELECT id, created_at, rows_returned FROM query_history`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Actual Result: rows=3836 columns=['id', 'created_at', 'rows_returned'] sample=[{'id': 1, 'created_at': '2026-06-08 13:46:02.803748', 'rows_returned': 3}, {'id': 2, 'created_at': '2026-06-08 13:46:02.842987', 'rows_returned': 4}]
  - Failure: Backend result set differs from expected SQL result.
- **S0061 (cold_cache, semantic, SELECT)**
  - NL: `List city, rating, vendor name for vendors.`
  - Expected SQL: `SELECT vendor_name, city, rating FROM vendors;`
  - Generated SQL: `SELECT city, id, vendor_name FROM vendors`
  - Executed SQL: `SELECT city, id, vendor_name FROM vendors`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['vendor_name', 'city', 'rating'] sample=[{'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Actual Result: rows=4 columns=['city', 'id', 'vendor_name'] sample=[{'city': 'Bangalore', 'id': 1, 'vendor_name': 'ABC Traders'}, {'city': 'Chennai', 'id': 2, 'vendor_name': 'Global Supplies'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0062 (cold_cache, semantic, SELECT)**
  - NL: `Display city, rating, vendor name for vendors.`
  - Expected SQL: `SELECT vendor_name, city, rating FROM vendors;`
  - Generated SQL: `SELECT id, vendor_name, city, rating FROM vendors;`
  - Executed SQL: `SELECT id, vendor_name, city, rating FROM vendors;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['vendor_name', 'city', 'rating'] sample=[{'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Actual Result: rows=4 columns=['id', 'vendor_name', 'city', 'rating'] sample=[{'id': 1, 'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'id': 2, 'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Failure: Backend result set differs from expected SQL result.
- **F0013 (warm_cache, functional, SELECT)**
  - NL: `Display vendor name, city, rating from vendors.`
  - Expected SQL: `SELECT vendor_name, city, rating FROM vendors;`
  - Generated SQL: `SELECT id, vendor_name, city, rating FROM vendors;`
  - Executed SQL: `SELECT id, vendor_name, city, rating FROM vendors;`
  - Validation: `valid` errors=[]
  - Expected Result: rows=4 columns=['vendor_name', 'city', 'rating'] sample=[{'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Actual Result: rows=4 columns=['id', 'vendor_name', 'city', 'rating'] sample=[{'id': 1, 'vendor_name': 'ABC Traders', 'city': 'Bangalore', 'rating': 4.5}, {'id': 2, 'vendor_name': 'Global Supplies', 'city': 'Chennai', 'rating': 4.2}]
  - Failure: Backend result set differs from expected SQL result.
- **S0006 (warm_cache, semantic, SELECT)**
  - NL: `List author id, title for books.`
  - Expected SQL: `SELECT title, author_id FROM books;`
  - Generated SQL: `SELECT book_id, title FROM books WHERE author_id IN ( SELECT author_id FROM authors )`
  - Executed SQL: `SELECT book_id, title FROM books WHERE author_id IN ( SELECT author_id FROM authors )`
  - Validation: `valid` errors=[]
  - Expected Result: rows=5 columns=['title', 'author_id'] sample=[{'title': 'Clean Code', 'author_id': 1}, {'title': 'Refactoring', 'author_id': 2}]
  - Actual Result: rows=5 columns=['book_id', 'title'] sample=[{'book_id': 1, 'title': 'Clean Code'}, {'book_id': 2, 'title': 'Refactoring'}]
  - Failure: Backend result set differs from expected SQL result.
### Backend rejected generated SQL request
- **F0110 (cold_cache, functional, AVG)**
  - NL: `What is the average salary in employees where salary is at least 4?`
  - Expected SQL: `SELECT AVG(salary) AS avg_salary FROM employees WHERE salary >= 4;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=1 columns=['avg_salary'] sample=[{'avg_salary': 74875.0}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
- **F0222 (cold_cache, functional, JOIN)**
  - NL: `List 11 matching employee projects and employees records.`
  - Expected SQL: `SELECT employee_projects.*, employees.employee_id FROM employee_projects JOIN employees ON employee_projects.employee_id = employees.employee_id WHERE employees.employee_id IS NOT NULL ORDER BY employee_projects.employee_id ASC LIMIT 11;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week', 'employee_id'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
- **F0268 (cold_cache, functional, HAVING)**
  - NL: `Find vendors grouped by city after applying count threshold 17.`
  - Expected SQL: `SELECT city, COUNT(*) AS row_count FROM vendors WHERE city IS NOT NULL AND LENGTH(city) >= 18 GROUP BY city HAVING COUNT(*) > 17 ORDER BY COUNT(*) DESC;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=0 columns=['city', 'row_count'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
- **S0253 (cold_cache, semantic, LIMIT)**
  - NL: `Give me a limited set of authors.`
  - Expected SQL: `SELECT author_id FROM authors LIMIT 3 OFFSET 0;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=3 columns=['author_id'] sample=[{'author_id': 1}, {'author_id': 2}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
- **S0260 (cold_cache, semantic, LIMIT)**
  - NL: `Fetch the limited books results.`
  - Expected SQL: `SELECT title, author_id FROM books LIMIT 4 OFFSET 1;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=4 columns=['title', 'author_id'] sample=[{'title': 'Refactoring', 'author_id': 2}, {'title': 'Modern Operating Systems', 'author_id': 3}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
- **S0264 (cold_cache, semantic, LIMIT)**
  - NL: `Please display this page of departments.`
  - Expected SQL: `SELECT location, department_id, department_name FROM departments LIMIT 5 OFFSET 2;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=3 columns=['location', 'department_id', 'department_name'] sample=[{'location': 'Chennai', 'department_id': 3, 'department_name': 'Finance'}, {'location': 'Hyderabad', 'department_id': 4, 'department_name': 'Marketing'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
- **S0265 (cold_cache, semantic, LIMIT)**
  - NL: `Fetch the limited departments results.`
  - Expected SQL: `SELECT location, department_id, department_name FROM departments LIMIT 5 OFFSET 2;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=3 columns=['location', 'department_id', 'department_name'] sample=[{'location': 'Chennai', 'department_id': 3, 'department_name': 'Finance'}, {'location': 'Hyderabad', 'department_id': 4, 'department_name': 'Marketing'}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
- **S0515 (cold_cache, semantic, COUNT)**
  - NL: `Return the employees results for this request: how many employees have salary is at least 22?`
  - Expected SQL: `SELECT COUNT(*) AS row_count FROM employees WHERE salary >= 22;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=1 columns=['row_count'] sample=[{'row_count': 8}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
- **S0779 (cold_cache, semantic, SUM)**
  - NL: `Please return the total for author id for authors.`
  - Expected SQL: `SELECT SUM(author_id) AS sum_author_id FROM authors WHERE author_name IS NOT NULL AND LENGTH(author_name) >= 1;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=1 columns=['sum_author_id'] sample=[{'sum_author_id': 10}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
- **S0829 (cold_cache, semantic, SUM)**
  - NL: `Please return the total for author id for books.`
  - Expected SQL: `SELECT SUM(author_id) AS sum_author_id FROM books WHERE author_id >= 10;`
  - Generated SQL: ``
  - Executed SQL: `None`
  - Validation: `unknown` errors=[]
  - Expected Result: rows=1 columns=['sum_author_id'] sample=[{'sum_author_id': None}]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend returned HTTP 400.
### Result-set mismatch
- **S0028 (cold_cache, semantic, SELECT)**
  - NL: `Which price, product id, product name for products are stored?`
  - Expected SQL: `SELECT price, product_id, product_name FROM products;`
  - Generated SQL: `SELECT price, product_id, product_name FROM products WHERE product_name = 'stored'`
  - Executed SQL: `SELECT price, product_id, product_name FROM products WHERE product_name = 'stored'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=2 columns=['price', 'product_id', 'product_name'] sample=[{'price': 49.99, 'product_id': 1, 'product_name': 'Analytics Pack'}, {'price': 19.99, 'product_id': 2, 'product_name': 'Cache Booster'}]
  - Actual Result: rows=0 columns=['price', 'product_id', 'product_name'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0037 (cold_cache, semantic, SELECT)**
  - NL: `Display created at, rows returned for query history.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history;`
  - Generated SQL: `SELECT rows_returned, created_at FROM query_history`
  - Executed SQL: `SELECT rows_returned, created_at FROM query_history`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Actual Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0038 (cold_cache, semantic, SELECT)**
  - NL: `Which created at, rows returned for query history are stored?`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history;`
  - Generated SQL: `SELECT created_at, rows_returned FROM query_history WHERE natural_language_query = 'Which created at, rows returned for query history are stored?'`
  - Executed SQL: `SELECT created_at, rows_returned FROM query_history WHERE natural_language_query = 'Which created at, rows returned for query history are stored?'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Actual Result: rows=2 columns=['created_at', 'rows_returned'] sample=[{'created_at': '2026-07-05 15:46:13.689804', 'rows_returned': 0}, {'created_at': '2026-07-05 15:54:40.733566', 'rows_returned': 0}]
  - Failure: Backend result set differs from expected SQL result.
- **F0008 (warm_cache, functional, SELECT)**
  - NL: `Display rows returned, created at from query history.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history;`
  - Generated SQL: `SELECT rows_returned, created_at FROM query_history`
  - Executed SQL: `SELECT rows_returned, created_at FROM query_history`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Actual Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0028 (warm_cache, semantic, SELECT)**
  - NL: `Which price, product id, product name for products are stored?`
  - Expected SQL: `SELECT price, product_id, product_name FROM products;`
  - Generated SQL: `SELECT price, product_id, product_name FROM products WHERE product_name = 'stored'`
  - Executed SQL: `SELECT price, product_id, product_name FROM products WHERE product_name = 'stored'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=2 columns=['price', 'product_id', 'product_name'] sample=[{'price': 49.99, 'product_id': 1, 'product_name': 'Analytics Pack'}, {'price': 19.99, 'product_id': 2, 'product_name': 'Cache Booster'}]
  - Actual Result: rows=0 columns=['price', 'product_id', 'product_name'] sample=[]
  - Failure: Backend result set differs from expected SQL result.
- **S0036 (warm_cache, semantic, SELECT)**
  - NL: `List created at, rows returned for query history.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history;`
  - Generated SQL: `SELECT created_at, rows_returned FROM query_history`
  - Executed SQL: `SELECT created_at, rows_returned FROM query_history`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Actual Result: rows=3836 columns=['created_at', 'rows_returned'] sample=[{'created_at': '2026-06-08 13:46:02.803748', 'rows_returned': 3}, {'created_at': '2026-06-08 13:46:02.842987', 'rows_returned': 4}]
  - Failure: Backend result set differs from expected SQL result.
- **S0037 (warm_cache, semantic, SELECT)**
  - NL: `Display created at, rows returned for query history.`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history;`
  - Generated SQL: `SELECT rows_returned, created_at FROM query_history`
  - Executed SQL: `SELECT rows_returned, created_at FROM query_history`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Actual Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Failure: Backend result set differs from expected SQL result.
- **S0038 (warm_cache, semantic, SELECT)**
  - NL: `Which created at, rows returned for query history are stored?`
  - Expected SQL: `SELECT rows_returned, created_at FROM query_history;`
  - Generated SQL: `SELECT created_at, rows_returned FROM query_history WHERE natural_language_query = 'Which created at, rows returned for query history are stored?'`
  - Executed SQL: `SELECT created_at, rows_returned FROM query_history WHERE natural_language_query = 'Which created at, rows returned for query history are stored?'`
  - Validation: `valid` errors=[]
  - Expected Result: rows=3836 columns=['rows_returned', 'created_at'] sample=[{'rows_returned': 3, 'created_at': '2026-06-08 13:46:02.803748'}, {'rows_returned': 4, 'created_at': '2026-06-08 13:46:02.842987'}]
  - Actual Result: rows=2 columns=['created_at', 'rows_returned'] sample=[{'created_at': '2026-07-05 15:46:13.689804', 'rows_returned': 0}, {'created_at': '2026-07-05 15:54:40.733566', 'rows_returned': 0}]
  - Failure: Backend result set differs from expected SQL result.
### Validation failure
- **S1109 (cold_cache, semantic, JOIN)**
  - NL: `Please return the joined employee projects and employees data.`
  - Expected SQL: `SELECT employee_projects.*, employees.employee_id FROM employee_projects JOIN employees ON employee_projects.employee_id = employees.employee_id WHERE employees.employee_id IS NOT NULL ORDER BY employee_projects.employee_id ASC LIMIT 11;`
  - Generated SQL: `SELECT e.employee_id, ep.project_id, ep.role FROM employees AS e INNER JOIN employee_projects AS ep ON e.employee_id = ep.employee_id UNION SELECT e1.employee_id, e2.department, e2.name FROM employees AS e1 LEFT JOIN employees AS e2 ON e1.department = e2.department`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['Only SELECT statements can be validated for execution.']
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week', 'employee_id'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S1114 (cold_cache, semantic, JOIN)**
  - NL: `Please return the joined employee projects and projects data.`
  - Expected SQL: `SELECT employee_projects.*, projects.project_id FROM employee_projects JOIN projects ON employee_projects.project_id = projects.project_id WHERE projects.project_id IS NOT NULL ORDER BY employee_projects.project_id ASC LIMIT 12;`
  - Generated SQL: `SELECT e.employee_id, ep.project_id, ep.role FROM employees AS e INNER JOIN employee_projects AS ep ON e.employee_id = ep.employee_id UNION SELECT e1.employee_id, e2.department, e2.name FROM employees AS e1 LEFT JOIN employees AS e2 ON e1.department = e2.department`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['Only SELECT statements can be validated for execution.']
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week', 'project_id'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S1109 (warm_cache, semantic, JOIN)**
  - NL: `Please return the joined employee projects and employees data.`
  - Expected SQL: `SELECT employee_projects.*, employees.employee_id FROM employee_projects JOIN employees ON employee_projects.employee_id = employees.employee_id WHERE employees.employee_id IS NOT NULL ORDER BY employee_projects.employee_id ASC LIMIT 11;`
  - Generated SQL: `SELECT e.employee_id, ep.project_id, ep.role FROM employees AS e INNER JOIN employee_projects AS ep ON e.employee_id = ep.employee_id UNION SELECT e1.employee_id, e2.department, e2.name FROM employees AS e1 LEFT JOIN employees AS e2 ON e1.department = e2.department`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['Only SELECT statements can be validated for execution.']
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week', 'employee_id'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.
- **S1114 (warm_cache, semantic, JOIN)**
  - NL: `Please return the joined employee projects and projects data.`
  - Expected SQL: `SELECT employee_projects.*, projects.project_id FROM employee_projects JOIN projects ON employee_projects.project_id = projects.project_id WHERE projects.project_id IS NOT NULL ORDER BY employee_projects.project_id ASC LIMIT 12;`
  - Generated SQL: `SELECT e.employee_id, ep.project_id, ep.role FROM employees AS e INNER JOIN employee_projects AS ep ON e.employee_id = ep.employee_id UNION SELECT e1.employee_id, e2.department, e2.name FROM employees AS e1 LEFT JOIN employees AS e2 ON e1.department = e2.department`
  - Executed SQL: `None`
  - Validation: `invalid` errors=['Only SELECT statements can be validated for execution.']
  - Expected Result: rows=0 columns=['employee_id', 'project_id', 'role', 'hours_per_week', 'project_id'] sample=[]
  - Actual Result: rows=None columns=[] sample=[]
  - Failure: Backend SQL validation failed.

