import { useEffect, useMemo, useState } from 'react';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import HistoryIcon from '@mui/icons-material/History';
import SearchIcon from '@mui/icons-material/Search';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import { Alert, Button, CircularProgress, Grid, InputAdornment, Stack, TextField } from '@mui/material';
import { getQueryHistory, type QueryHistoryRecord } from '../api/history';
import { CodeBlock, DataTable, FilterBar, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function QueryHistoryPage() {
  const [historyRecords, setHistoryRecords] = useState<QueryHistoryRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadHistory() {
      try {
        setIsLoading(true);
        setError(null);
        const response = await getQueryHistory(100);
        setHistoryRecords(response.items);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : 'Failed to load query history');
      } finally {
        setIsLoading(false);
      }
    }

    void loadHistory();

    return () => controller.abort();
  }, []);

  const filteredRecords = useMemo(() => {
    const normalizedSearchTerm = searchTerm.trim().toLowerCase();
    if (!normalizedSearchTerm) {
      return historyRecords;
    }

    return historyRecords.filter((record) => (
      record.natural_language_query.toLowerCase().includes(normalizedSearchTerm)
      || record.generated_sql.toLowerCase().includes(normalizedSearchTerm)
      || record.generation_mode.toLowerCase().includes(normalizedSearchTerm)
      || record.cache_status.toLowerCase().includes(normalizedSearchTerm)
      || record.validation_status.toLowerCase().includes(normalizedSearchTerm)
    ));
  }, [historyRecords, searchTerm]);

  const selectedRecord = filteredRecords[0] ?? historyRecords[0];
  const totalQueries = historyRecords.length;
  const successfulQueries = historyRecords.filter((record) => record.validation_status.toLowerCase() === 'valid').length;
  const failedQueries = totalQueries - successfulQueries;
  const cacheHits = historyRecords.filter((record) => record.cache_status.toLowerCase() === 'hit').length;
  const averageExecutionTime = totalQueries > 0
    ? historyRecords.reduce((total, record) => total + record.execution_time, 0) / totalQueries
    : 0;
  const cacheHitRate = totalQueries > 0 ? (cacheHits / totalQueries) * 100 : 0;

  const statCards = [
    { label: 'Total Queries', value: totalQueries.toLocaleString(), icon: HistoryIcon, trend: 'Live history records', tone: 'purple' },
    { label: 'Successful Queries', value: successfulQueries.toLocaleString(), icon: CheckCircleOutlineIcon, trend: 'Validation status: valid', tone: 'green' },
    { label: 'Avg Execution Time', value: `${averageExecutionTime.toFixed(3)} sec`, icon: SpeedIcon, trend: 'Across latest records', tone: 'orange' },
    { label: 'Cache Hit Rate', value: `${cacheHitRate.toFixed(1)}%`, icon: StorageIcon, trend: `${cacheHits} cache hits`, tone: 'blue' },
    { label: 'Failed Queries', value: failedQueries.toLocaleString(), icon: ErrorOutlineIcon, trend: 'Validation status: invalid', trendDirection: 'down', tone: 'red' }
  ];

  const historyRows = filteredRecords.map((record, index) => [
    String(index + 1),
    record.natural_language_query,
    previewSql(record.generated_sql),
    <StatusBadge label={record.validation_status.toLowerCase() === 'valid' ? 'Success' : 'Failed'} tone={record.validation_status.toLowerCase() === 'valid' ? 'green' : 'red'} />,
    <StatusBadge label={record.cache_status} tone={record.cache_status.toLowerCase() === 'hit' ? 'green' : 'red'} />,
    `${record.execution_time.toFixed(3)} sec`,
    record.generation_mode,
    formatHistoryTime(record.created_at)
  ]);

  return (
    <>
      <PageHeader title="Query History" description="Search and audit natural language prompts, generated SQL, execution metadata, and cache outcomes." />
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}
      <Grid container spacing={2.5}>
        {statCards.map((stat) => (
          <Grid item key={stat.label} md={2.4} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}
        <Grid item xs={12}>
          <FilterBar items={['All Users', 'All Status', 'All Cache Status', 'All Query Types']} />
        </Grid>
        <Grid item md={8.5} xs={12}>
          <Panel
            action={<Button variant="outlined">Export CSV</Button>}
            title="Searchable History Table"
          >
            <TextField
              fullWidth
              InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> }}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search queries, SQL, users, or keywords..."
              size="small"
              sx={{ mb: 2 }}
              value={searchTerm}
            />
            {isLoading ? <CircularProgress size={22} /> : (
              <DataTable columns={['#', 'Natural Language Query', 'Generated SQL Preview', 'Status', 'Cache', 'Execution', 'Mode', 'Time']} rows={historyRows.length > 0 ? historyRows : [['-', 'No query history records yet', '-', '-', '-', '-', '-', '-']]} />
            )}
          </Panel>
        </Grid>
        <Grid item md={3.5} xs={12}>
          <Stack spacing={2.5}>
            <Panel title="Execution Metadata">
              <DataTable columns={['Field', 'Value']} rows={selectedRecord ? [
                ['Query ID', `QRY-${selectedRecord.id.toString().padStart(6, '0')}`],
                ['Generation Mode', selectedRecord.generation_mode],
                ['Status', <StatusBadge label={selectedRecord.validation_status.toLowerCase() === 'valid' ? 'Success' : 'Failed'} tone={selectedRecord.validation_status.toLowerCase() === 'valid' ? 'green' : 'red'} />],
                ['Cache Status', <StatusBadge label={selectedRecord.cache_status} tone={selectedRecord.cache_status.toLowerCase() === 'hit' ? 'green' : 'red'} />],
                ['Rows Returned', selectedRecord.rows_returned],
                ['Execution Time', `${selectedRecord.execution_time.toFixed(3)} sec`]
              ] : [['Query ID', '-'], ['Generation Mode', '-'], ['Status', '-'], ['Rows Returned', '-'], ['Execution Time', '-']]} />
            </Panel>
            <Panel title="SQL Preview">
              <CodeBlock code={selectedRecord?.generated_sql ?? 'No query selected'} />
            </Panel>
          </Stack>
        </Grid>
      </Grid>
    </>
  );
}

function previewSql(sql: string) {
  return sql.length > 64 ? `${sql.slice(0, 64)}...` : sql;
}

function formatHistoryTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }

  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
