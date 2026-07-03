import { useEffect, useMemo, useState } from 'react';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HistoryIcon from '@mui/icons-material/History';
import MemoryIcon from '@mui/icons-material/Memory';
import RefreshIcon from '@mui/icons-material/Refresh';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { Alert, Button, CircularProgress, Grid, Stack, Typography } from '@mui/material';
import { getSystemMonitorMetrics, type SystemMonitorResponse } from '../api/systemMonitor';
import { DataTable, DonutChart, LineChart, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

const emptyMonitor: SystemMonitorResponse = {
  total_queries: 0,
  successful_queries: 0,
  failed_queries: 0,
  cache_hits: 0,
  cache_misses: 0,
  cache_hit_rate: 0,
  average_execution_time: 0,
  schema_mismatches: 0,
  llm_queries: 0,
  rule_queries: 0,
  recent_failures: [],
  recent_activity: [],
  query_volume_trend: []
};

export function SystemMonitorPage() {
  const [monitor, setMonitor] = useState<SystemMonitorResponse>(emptyMonitor);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadMonitor() {
    try {
      setIsLoading(true);
      setError(null);
      setMonitor(await getSystemMonitorMetrics());
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Failed to load system monitor metrics');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadMonitor();
  }, []);

  const hasHistory = monitor.total_queries > 0;
  const successRate = monitor.total_queries > 0 ? (monitor.successful_queries / monitor.total_queries) * 100 : 0;
  const volumeData = monitor.query_volume_trend.map((point) => point.count);
  const volumeLabels = monitor.query_volume_trend.map((point) => formatDateLabel(point.date));
  const recentFailureRows = useMemo(() => monitor.recent_failures.map((failure) => [
    failure.natural_language_query,
    previewSql(failure.generated_sql),
    <StatusBadge key={failure.created_at} label={failure.failure_type} tone={failure.failure_type === 'Schema Mismatch' ? 'red' : 'orange'} />,
    formatTimestamp(failure.created_at)
  ]), [monitor.recent_failures]);
  const recentActivityRows = useMemo(() => monitor.recent_activity.map((record) => [
    record.natural_language_query,
    record.generation_mode,
    <StatusBadge key={`${record.id}-validation`} label={record.validation_status} tone={record.validation_status.toLowerCase() === 'valid' ? 'green' : 'red'} />,
    <StatusBadge key={`${record.id}-cache`} label={record.cache_status} tone={record.cache_status.toLowerCase() === 'hit' ? 'green' : 'red'} />,
    `${record.execution_time.toFixed(3)} sec`,
    formatTimestamp(record.created_at)
  ]), [monitor.recent_activity]);

  return (
    <>
      <PageHeader title="System Monitor" description="Monitor SemanticSQL query activity, validation outcomes, cache behavior, and recent failures." />
      {error ? (
        <Alert
          action={<Button color="inherit" onClick={() => void loadMonitor()} size="small">Retry</Button>}
          severity="error"
          sx={{ mb: 2 }}
        >
          {error}
        </Alert>
      ) : null}

      {isLoading ? (
        <Stack spacing={2} sx={{ alignItems: 'center', py: 6 }}>
          <CircularProgress size={28} />
          <Typography color="text.secondary" variant="body2">
            Loading monitoring metrics...
          </Typography>
        </Stack>
      ) : !hasHistory ? (
        <Panel title="No Query History">
          <Typography color="text.secondary" variant="body2">
            No query history available.
            Run queries from Query Interface to populate monitoring metrics.
          </Typography>
        </Panel>
      ) : (
        <Grid container spacing={2.5}>
          {[
            { label: 'Total Queries', value: monitor.total_queries.toLocaleString(), icon: HistoryIcon, trend: 'From query history', tone: 'blue' },
            { label: 'Success Rate', value: `${successRate.toFixed(1)}%`, icon: CheckCircleOutlineIcon, trend: `${monitor.successful_queries} valid / ${monitor.failed_queries} invalid`, tone: 'green' },
            { label: 'Cache Hit Rate', value: `${monitor.cache_hit_rate.toFixed(1)}%`, icon: StorageIcon, trend: `${monitor.cache_hits} hits / ${monitor.cache_misses} misses`, tone: 'purple' },
            { label: 'Average Execution Time', value: `${monitor.average_execution_time.toFixed(3)} sec`, icon: SpeedIcon, trend: 'Across query history', tone: 'orange' },
            { label: 'LLM Queries', value: monitor.llm_queries.toLocaleString(), icon: MemoryIcon, trend: `${monitor.rule_queries} Rule queries`, tone: 'cyan' },
            { label: 'Schema Mismatches', value: monitor.schema_mismatches.toLocaleString(), icon: WarningAmberIcon, trend: 'SCHEMA_MISMATCH records', trendDirection: 'down', tone: 'red' }
          ].map((stat) => (
            <Grid item key={stat.label} md={2} sm={6} xs={12}>
              <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
            </Grid>
          ))}

          <Grid item md={6} xs={12}>
            <Panel action={<Button onClick={() => void loadMonitor()} startIcon={<RefreshIcon />} variant="outlined">Refresh</Button>} title="Query Activity Trend">
              {volumeData.length > 0 ? <LineChart data={volumeData} labels={volumeLabels} /> : <EmptyState />}
            </Panel>
          </Grid>
          <Grid item md={3} xs={12}>
            <Panel title="Query Outcome Breakdown">
              <DonutChart centerLabel={monitor.total_queries.toString()} segments={[
                { label: 'Success', value: percent(monitor.successful_queries, monitor.total_queries), color: '#16a34a' },
                { label: 'Failure', value: percent(monitor.failed_queries, monitor.total_queries), color: '#ef4444' }
              ]} />
            </Panel>
          </Grid>
          <Grid item md={3} xs={12}>
            <Panel title="Cache Performance">
              <DonutChart centerLabel={monitor.total_queries.toString()} segments={[
                { label: 'Hits', value: percent(monitor.cache_hits, monitor.total_queries), color: '#2563eb' },
                { label: 'Misses', value: percent(monitor.cache_misses, monitor.total_queries), color: '#f59e0b' }
              ]} />
            </Panel>
          </Grid>

          <Grid item md={5} xs={12}>
            <Panel title="Recent Failures">
              <DataTable
                columns={['Natural Language Query', 'Generated SQL', 'Failure Type', 'Timestamp']}
                rows={recentFailureRows.length > 0 ? recentFailureRows : [['No recent failures', '-', '-', '-']]}
              />
            </Panel>
          </Grid>
          <Grid item md={7} xs={12}>
            <Panel title="Recent Activity">
              <DataTable
                columns={['Natural Language Query', 'Generation Mode', 'Validation Status', 'Cache Status', 'Execution Time', 'Timestamp']}
                rows={recentActivityRows.length > 0 ? recentActivityRows : [['No recent activity', '-', '-', '-', '-', '-']]}
              />
            </Panel>
          </Grid>
        </Grid>
      )}
    </>
  );
}

function percent(value: number, total: number) {
  return total > 0 ? Number(((value / total) * 100).toFixed(1)) : 0;
}

function previewSql(sql: string) {
  return sql.length > 72 ? `${sql.slice(0, 72)}...` : sql;
}

function formatDateLabel(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function EmptyState() {
  return (
    <Typography color="text.secondary" variant="body2">
      No query history available.
    </Typography>
  );
}
