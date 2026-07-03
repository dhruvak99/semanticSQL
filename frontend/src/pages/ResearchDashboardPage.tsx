import { useEffect, useMemo, useState } from 'react';
import MemoryIcon from '@mui/icons-material/Memory';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import RefreshIcon from '@mui/icons-material/Refresh';
import RuleIcon from '@mui/icons-material/Rule';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { Alert, Button, CircularProgress, Grid, Stack, Typography } from '@mui/material';
import { getResearchAnalytics, type ResearchAnalyticsResponse } from '../api/research';
import { DataTable, DonutChart, LineChart, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

const emptyAnalytics: ResearchAnalyticsResponse = {
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
  volume_trend: [],
  recent_queries: []
};

export function ResearchDashboardPage() {
  const [analytics, setAnalytics] = useState<ResearchAnalyticsResponse>(emptyAnalytics);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadAnalytics() {
    try {
      setIsLoading(true);
      setError(null);
      setAnalytics(await getResearchAnalytics());
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Failed to load research analytics');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadAnalytics();
  }, []);

  const hasHistory = analytics.total_queries > 0;
  const successRate = percent(analytics.successful_queries, analytics.total_queries);
  const volumeData = analytics.volume_trend.map((point) => point.count);
  const volumeLabels = analytics.volume_trend.map((point) => formatDateLabel(point.date));
  const datasetRows = useMemo(() => analytics.recent_queries.map((record) => [
    record.natural_language_query,
    record.generation_mode,
    <StatusBadge key={`${record.id}-cache`} label={record.cache_status} tone={record.cache_status.toLowerCase() === 'hit' ? 'green' : 'red'} />,
    <StatusBadge key={`${record.id}-validation`} label={record.validation_status} tone={record.validation_status.toLowerCase() === 'valid' ? 'green' : 'red'} />,
    `${record.execution_time.toFixed(3)} sec`,
    formatTimestamp(record.created_at)
  ]), [analytics.recent_queries]);

  return (
    <>
      <PageHeader title="Research Dashboard" description="Evaluate SemanticSQL cache effectiveness, generation behavior, validation outcomes, and execution history." />
      {error ? (
        <Alert
          action={<Button color="inherit" onClick={() => void loadAnalytics()} size="small">Retry</Button>}
          severity="error"
          sx={{ mb: 2 }}
        >
          {error}
        </Alert>
      ) : null}

      {isLoading ? (
        <Stack spacing={2} sx={{ alignItems: 'center', py: 6 }}>
          <CircularProgress size={28} />
          <Typography color="text.secondary" variant="body2">Loading research analytics...</Typography>
        </Stack>
      ) : !hasHistory ? (
        <Panel title="No Research Data">
          <Typography color="text.secondary" variant="body2">
            No query history available.
            Run queries from Query Interface to populate research analytics.
          </Typography>
        </Panel>
      ) : (
        <Grid container spacing={2.5}>
          {[
            { label: 'Total Queries', value: analytics.total_queries.toLocaleString(), icon: QueryStatsIcon, trend: 'Persisted query history', tone: 'blue' },
            { label: 'Cache Hit Rate', value: `${analytics.cache_hit_rate.toFixed(1)}%`, icon: StorageIcon, trend: `${analytics.cache_hits} hits / ${analytics.cache_misses} misses`, tone: 'green' },
            { label: 'Average Execution Time', value: `${analytics.average_execution_time.toFixed(3)} sec`, icon: SpeedIcon, trend: 'Across query history', tone: 'orange' },
            { label: 'LLM Queries', value: analytics.llm_queries.toLocaleString(), icon: MemoryIcon, trend: 'LLM generation path', tone: 'purple' },
            { label: 'Rule Queries', value: analytics.rule_queries.toLocaleString(), icon: RuleIcon, trend: 'Rule generation path', tone: 'cyan' },
            { label: 'Schema Mismatches', value: analytics.schema_mismatches.toLocaleString(), icon: WarningAmberIcon, trend: 'SCHEMA_MISMATCH records', trendDirection: 'down', tone: 'red' }
          ].map((stat) => (
            <Grid item key={stat.label} md={2} sm={6} xs={12}>
              <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
            </Grid>
          ))}

          <Grid item md={4} xs={12}>
            <Panel subtitle={`${analytics.cache_hits} hits, ${analytics.cache_misses} misses`} title="Semantic Cache Evaluation">
              <DonutChart centerLabel={`${analytics.cache_hit_rate.toFixed(1)}%`} segments={[
                { label: 'Cache Hits', value: percent(analytics.cache_hits, analytics.total_queries), color: '#16a34a' },
                { label: 'Cache Misses', value: percent(analytics.cache_misses, analytics.total_queries), color: '#ef4444' }
              ]} />
            </Panel>
          </Grid>
          <Grid item md={4} xs={12}>
            <Panel subtitle={`${analytics.llm_queries} LLM, ${analytics.rule_queries} Rule`} title="Query Generation Analysis">
              <DonutChart centerLabel={analytics.total_queries.toString()} segments={[
                { label: 'LLM', value: percent(analytics.llm_queries, analytics.total_queries), color: '#7c3aed' },
                { label: 'Rule', value: percent(analytics.rule_queries, analytics.total_queries), color: '#0891b2' }
              ]} />
            </Panel>
          </Grid>
          <Grid item md={4} xs={12}>
            <Panel subtitle={`${analytics.successful_queries} successful, ${analytics.failed_queries} failed`} title="Query Outcome Analysis">
              <DonutChart centerLabel={`${successRate.toFixed(1)}%`} segments={[
                { label: 'Success', value: successRate, color: '#16a34a' },
                { label: 'Failure', value: percent(analytics.failed_queries, analytics.total_queries), color: '#ef4444' }
              ]} />
            </Panel>
          </Grid>

          <Grid item xs={12}>
            <Panel action={<Button onClick={() => void loadAnalytics()} startIcon={<RefreshIcon />} variant="outlined">Refresh</Button>} title="Query Volume Trend">
              {analytics.volume_trend.length >= 2 ? (
                <LineChart data={volumeData} labels={volumeLabels} />
              ) : (
                <Typography color="text.secondary" variant="body2">
                  Insufficient history for trend analysis
                </Typography>
              )}
            </Panel>
          </Grid>

          <Grid item xs={12}>
            <Panel title="Research Dataset">
              <DataTable
                columns={['Natural Language Query', 'Generation Mode', 'Cache Status', 'Validation Status', 'Execution Time', 'Timestamp']}
                rows={datasetRows.length > 0 ? datasetRows : [['No query history records available', '-', '-', '-', '-', '-']]}
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

function formatDateLabel(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}
