import { useEffect, useMemo, useState } from 'react';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import MemoryIcon from '@mui/icons-material/Memory';
import RefreshIcon from '@mui/icons-material/Refresh';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { Alert, Button, CircularProgress, Grid, Stack, Typography } from '@mui/material';
import { getDashboardMetrics, type DashboardResponse } from '../api/dashboard';
import { DataTable, LineChart, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

const emptyDashboard: DashboardResponse = {
  total_queries: 0,
  successful_queries: 0,
  failed_queries: 0,
  cache_hits: 0,
  cache_misses: 0,
  cache_hit_rate: 0,
  average_execution_time: 0,
  llm_queries: 0,
  rule_queries: 0,
  schema_mismatches: 0,
  recent_queries: [],
  query_volume_trend: []
};

export function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardResponse>(emptyDashboard);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDashboard() {
    try {
      setIsLoading(true);
      setError(null);
      setDashboard(await getDashboardMetrics());
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Failed to load dashboard metrics');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  const hasHistory = dashboard.total_queries > 0;
  const successRate = dashboard.total_queries > 0
    ? (dashboard.successful_queries / dashboard.total_queries) * 100
    : 0;
  const volumeData = dashboard.query_volume_trend.map((point) => point.count);
  const volumeLabels = dashboard.query_volume_trend.map((point) => formatDateLabel(point.date));
  const recentRows = useMemo(() => dashboard.recent_queries.map((record) => [
    record.natural_language_query,
    record.generation_mode,
    <StatusBadge label={record.validation_status} tone={record.validation_status.toLowerCase() === 'valid' ? 'green' : 'red'} />,
    <StatusBadge label={record.cache_status} tone={record.cache_status.toLowerCase() === 'hit' ? 'green' : 'red'} />,
    `${record.execution_time.toFixed(3)} sec`,
    formatTimestamp(record.created_at)
  ]), [dashboard.recent_queries]);

  return (
    <>
      <PageHeader title="Dashboard" description="Live query history metrics, cache outcomes, generation mix, and recent SemanticSQL activity." />
      {error ? (
        <Alert
          action={<Button color="inherit" onClick={() => void loadDashboard()} size="small">Retry</Button>}
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
            Loading dashboard metrics...
          </Typography>
        </Stack>
      ) : !hasHistory ? (
        <Panel title="No Query History">
          <Typography color="text.secondary" variant="body2">
            No query history available yet.
            Run queries from Query Interface to populate dashboard metrics.
          </Typography>
        </Panel>
      ) : (
        <Grid container spacing={2.5}>
          {[
            { label: 'Total Queries', value: dashboard.total_queries.toLocaleString(), icon: ChatBubbleOutlineIcon, trend: 'From query history', tone: 'blue' },
            { label: 'Success Rate', value: `${successRate.toFixed(1)}%`, icon: CheckCircleOutlineIcon, trend: `${dashboard.successful_queries} valid / ${dashboard.failed_queries} invalid`, tone: 'green' },
            { label: 'Cache Hit Rate', value: `${dashboard.cache_hit_rate.toFixed(1)}%`, icon: StorageIcon, trend: `${dashboard.cache_hits} hits / ${dashboard.cache_misses} misses`, tone: 'purple' },
            { label: 'Average Execution Time', value: `${dashboard.average_execution_time.toFixed(3)} sec`, icon: SpeedIcon, trend: 'Across query history', tone: 'orange' },
            { label: 'LLM Queries', value: dashboard.llm_queries.toLocaleString(), icon: MemoryIcon, trend: `${dashboard.rule_queries} Rule queries`, tone: 'cyan' },
            { label: 'Schema Mismatches', value: dashboard.schema_mismatches.toLocaleString(), icon: WarningAmberIcon, trend: 'SCHEMA_MISMATCH records', trendDirection: 'down', tone: 'red' }
          ].map((stat) => (
            <Grid item key={stat.label} md={2} sm={6} xs={12}>
              <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
            </Grid>
          ))}

          <Grid item md={7} xs={12}>
            <Panel action={<Button onClick={() => void loadDashboard()} startIcon={<RefreshIcon />} variant="outlined">Refresh</Button>} title="Query Volume Trend">
              {volumeData.length > 0 ? (
                <LineChart data={volumeData} labels={volumeLabels} />
              ) : (
                <EmptyState />
              )}
            </Panel>
          </Grid>

          <Grid item md={5} xs={12}>
            <Panel title="Dashboard Summary">
              <DataTable columns={['Metric', 'Value']} rows={[
                ['Successful Queries', dashboard.successful_queries.toLocaleString()],
                ['Failed Queries', dashboard.failed_queries.toLocaleString()],
                ['Cache Hits', dashboard.cache_hits.toLocaleString()],
                ['Cache Misses', dashboard.cache_misses.toLocaleString()],
                ['Rule Queries', dashboard.rule_queries.toLocaleString()],
                ['LLM Queries', dashboard.llm_queries.toLocaleString()]
              ]} />
            </Panel>
          </Grid>

          <Grid item xs={12}>
            <Panel title="Recent Activity">
              <DataTable
                columns={['Natural Language Query', 'Generation Mode', 'Validation Status', 'Cache Status', 'Execution Time', 'Timestamp']}
                rows={recentRows.length > 0 ? recentRows : [['No recent query history records', '-', '-', '-', '-', '-']]}
              />
            </Panel>
          </Grid>
        </Grid>
      )}
    </>
  );
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
      No query history available yet.
    </Typography>
  );
}
