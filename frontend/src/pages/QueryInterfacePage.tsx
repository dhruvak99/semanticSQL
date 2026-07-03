import { useMemo, useState } from 'react';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { Alert, Button, CircularProgress, Grid, Stack, TextField, Typography } from '@mui/material';
import { processQuery, type QueryProcessResponse, type QueryResultRow } from '../api/query';
import { CodeBlock, DataTable, Panel, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

const defaultQuery =
  'Show employees with salary greater than 50000';

const initialResponse: QueryProcessResponse = {
  generation_mode: 'Rule',
  generated_sql:
    'SELECT employee_id, name, email, department, salary, joining_date\nFROM employees\nWHERE salary > 50000\nORDER BY salary DESC;',
  corrected_sql: null,
  executed_sql: 'SELECT employee_id, name, email, department, salary, joining_date\nFROM employees\nWHERE salary > 50000\nORDER BY salary DESC;',
  validation: {
    valid: true,
    errors: []
  },
  cache_hit: false,
  similarity_score: 0,
  validation_status: 'valid',
  validation_errors: [],
  execution_time: 0.42,
  rows_returned: 18,
  results: [
    {
      employee_id: 107,
      name: 'Michael Brown',
      email: 'michael.brown@company.com',
      department: 'Finance',
      salary: 95000,
      joining_date: '2021-05-10'
    },
    {
      employee_id: 104,
      name: 'Sarah Johnson',
      email: 'sarah.johnson@company.com',
      department: 'Finance',
      salary: 88000,
      joining_date: '2020-03-22'
    }
  ]
};

function formatCellValue(value: QueryResultRow[string]) {
  if (value === null) {
    return 'NULL';
  }

  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }

  return String(value);
}

export function QueryInterfacePage() {
  const [query, setQuery] = useState(defaultQuery);
  const [response, setResponse] = useState<QueryProcessResponse>(initialResponse);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const resultColumns = useMemo(() => {
    const firstRow = response.results[0];
    return firstRow ? Object.keys(firstRow) : ['message'];
  }, [response.results]);

  const resultRows = useMemo(() => {
    if (response.results.length === 0) {
      return [['No rows returned']];
    }

    return response.results.map((row) => resultColumns.map((column) => formatCellValue(row[column])));
  }, [response.results, resultColumns]);

  const pipelineSteps = [
    { label: 'Semantic Cache Check', detail: `${response.cache_hit ? 'Cache hit' : 'Cache miss'} · score ${response.similarity_score.toFixed(2)}`, tone: response.cache_hit ? 'green' : 'orange' },
    { label: 'SQL Generation', detail: `${response.generation_mode} generator completed`, tone: response.generation_mode === 'Rule' ? 'blue' : 'purple' },
    { label: 'SQL Validation', detail: response.validation_errors.length > 0 ? `${response.validation_status} · ${response.validation_errors.length} errors` : response.validation_status, tone: response.validation_status === 'valid' ? 'green' : 'red' },
    { label: 'SQL Correction', detail: response.corrected_sql ? 'Correction applied' : 'No correction applied', tone: response.corrected_sql ? 'purple' : 'gray' },
    { label: 'Execution', detail: response.executed_sql ? `${response.execution_time.toFixed(2)} sec` : 'Skipped', tone: response.executed_sql ? 'blue' : 'orange' },
    { label: 'Response', detail: `${response.rows_returned} rows`, tone: 'green' }
  ] as const;

  async function handleRunQuery() {
    setIsLoading(true);
    setError(null);

    try {
      const processedQuery = await processQuery(query);
      setResponse(processedQuery);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Failed to process query');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <>
      <PageHeader title="Query Interface" description="Translate business questions into SQL, validate them, correct schema drift, and inspect results." />
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}
      <Grid container spacing={2.5}>
        <Grid item md={8} xs={12}>
          <Panel
            action={
              <Button disabled={isLoading || query.trim().length === 0} onClick={handleRunQuery} startIcon={isLoading ? <CircularProgress color="inherit" size={18} /> : <PlayArrowIcon />}>
                {isLoading ? 'Running' : 'Run Query'}
              </Button>
            }
            title="Natural Language Input"
          >
            <TextField
              fullWidth
              multiline
              minRows={5}
              onChange={(event) => setQuery(event.target.value)}
              value={query}
            />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Query Pipeline">
            <Stack spacing={1.5}>
              {pipelineSteps.map((step, index) => (
                <Stack direction="row" key={step.label} spacing={1.5} sx={{ alignItems: 'center' }}>
                  <StatusBadge label={`${index + 1}`} tone={step.tone} />
                  <Stack sx={{ flexGrow: 1 }}>
                    <Typography variant="body2">{step.label}</Typography>
                    <Typography color="text.secondary" variant="caption">{step.detail}</Typography>
                  </Stack>
                  {response.validation_status === 'invalid' && step.label === 'SQL Validation' ? <ErrorOutlineIcon color="error" fontSize="small" /> : <CheckCircleIcon color="success" fontSize="small" />}
                </Stack>
              ))}
            </Stack>
          </Panel>
        </Grid>
        <Grid item md={8} xs={12}>
          <Panel action={<Button startIcon={<ContentCopyIcon />} variant="outlined">Copy</Button>} title="Generated SQL Panel">
            <CodeBlock code={response.generated_sql} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Execution Metadata">
            <DataTable columns={['Metric', 'Value']} rows={[
              ['Pipeline', 'SemanticSQL Mock v1'],
              ['Execution Time', `${response.execution_time.toFixed(2)} sec`],
              ['Rows Returned', response.rows_returned],
              ['Generation Mode', <StatusBadge label={response.generation_mode} tone={response.generation_mode === 'Rule' ? 'blue' : 'purple'} />],
              ['Cache Status', <StatusBadge label={response.cache_hit ? 'Hit' : 'Miss'} tone={response.cache_hit ? 'green' : 'red'} />],
              ['Similarity Score', response.similarity_score.toFixed(4)],
              ['Validation', <StatusBadge label={response.validation_status} tone={response.validation_status === 'valid' ? 'green' : 'red'} />],
              ['Validation Errors Count', response.validation_errors.length],
              ['Model Used', response.generation_mode === 'Rule' ? 'Rule SQL generator' : 'llama3.1:8b']
            ]} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Validation Panel">
            <Stack spacing={1.5}>
              <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography fontWeight={700} variant="body2">
                  {response.validation.valid ? 'Validation Passed' : 'Validation Failed'}
                </Typography>
                <StatusBadge label={response.validation.valid ? 'Valid' : 'Invalid'} tone={response.validation.valid ? 'green' : 'red'} />
              </Stack>
              {response.validation.errors.length > 0 ? (
                <Stack spacing={0.75}>
                  <Typography color="text.secondary" variant="caption">Errors</Typography>
                  {response.validation.errors.map((validationError) => (
                    <Alert key={validationError} severity="error" variant="outlined">
                      {validationError}
                    </Alert>
                  ))}
                </Stack>
              ) : (
                <Alert severity="success" variant="outlined">Validation passed.</Alert>
              )}
            </Stack>
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Correction Panel">
            {response.corrected_sql ? (
              <Stack spacing={1.25}>
                <Typography color="text.secondary" variant="caption">Original SQL</Typography>
                <CodeBlock code={response.generated_sql} />
                <Typography color="text.secondary" textAlign="center" variant="body2">↓</Typography>
                <Typography color="text.secondary" variant="caption">Corrected SQL</Typography>
                <CodeBlock code={response.corrected_sql} />
              </Stack>
            ) : (
              <Alert severity="info" variant="outlined">No SQL correction was applied.</Alert>
            )}
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Executed SQL">
            {response.executed_sql ? (
              <CodeBlock dark code={response.executed_sql} />
            ) : (
              <Alert severity="warning" variant="outlined">Execution skipped due to validation failure.</Alert>
            )}
          </Panel>
        </Grid>
        <Grid item xs={12}>
          <Panel title="Results Table">
            <DataTable columns={resultColumns} rows={resultRows} />
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
