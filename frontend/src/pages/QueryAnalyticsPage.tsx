import { useEffect, useMemo, useState } from 'react';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { Alert, CircularProgress, Grid, Typography } from '@mui/material';
import { getQueryAnalytics, type QueryAnalyticsResponse } from '../api/history';
import { DataTable, DonutChart, LineChart, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

const emptyAnalytics: QueryAnalyticsResponse = {
  total_queries: 0,
  successful_queries: 0,
  failed_queries: 0,
  cache_hits: 0,
  cache_misses: 0,
  cache_hit_rate: 0,
  average_execution_time: 0,
  rule_generation_count: 0,
  llm_generation_count: 0,
  schema_mismatch_count: 0,
  volume_trend: [],
  recent_queries: []
};

export function QueryAnalyticsPage() {
  const [analytics, setAnalytics] = useState<QueryAnalyticsResponse>(emptyAnalytics);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setIsLoading(true);
        setError(null);
        setAnalytics(await getQueryAnalytics());
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : 'Failed to load query analytics');
      } finally {
        setIsLoading(false);
      }
    }

    void loadAnalytics();
  }, []);

  const hasHistory = analytics.total_queries > 0;
  const volumeData = analytics.volume_trend.map((point) => point.count);
  const volumeLabels = analytics.volume_trend.map((point) => formatDateLabel(point.date));
  const recentRows = useMemo(() => analytics.recent_queries.map((record) => [
    record.natural_language_query,
    record.generation_mode,
    <StatusBadge label={record.validation_status} tone={record.validation_status.toLowerCase() === 'valid' ? 'green' : 'red'} />,
    <StatusBadge label={record.cache_status} tone={record.cache_status.toLowerCase() === 'hit' ? 'green' : 'red'} />,
    `${record.execution_time.toFixed(3)} sec`,
    formatTimestamp(record.created_at)
  ]), [analytics.recent_queries]);

  return (
    <>
      <PageHeader title="Query Analytics" description="Analyze real query outcomes, cache behavior, generation modes, and recent execution history." />
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}
      <Grid container spacing={2.5}>
        {[
          { label: 'Total Queries', value: analytics.total_queries.toLocaleString(), icon: QueryStatsIcon, trend: 'From query history', tone: 'blue' },
          { label: 'Successful Queries', value: analytics.successful_queries.toLocaleString(), icon: CheckCircleOutlineIcon, trend: 'Validation status: valid', tone: 'green' },
          { label: 'Failed Queries', value: analytics.failed_queries.toLocaleString(), icon: ErrorOutlineIcon, trend: 'Validation status: invalid', trendDirection: 'down', tone: 'red' },
          { label: 'Cache Hit Rate', value: `${analytics.cache_hit_rate.toFixed(1)}%`, icon: StorageIcon, trend: `${analytics.cache_hits} hits / ${analytics.cache_misses} misses`, tone: 'purple' },
          { label: 'Avg Execution Time', value: `${analytics.average_execution_time.toFixed(3)} sec`, icon: SpeedIcon, trend: 'Across history', tone: 'orange' },
          { label: 'Schema Mismatches', value: analytics.schema_mismatch_count.toLocaleString(), icon: WarningAmberIcon, trend: 'SCHEMA_MISMATCH results', trendDirection: 'down', tone: 'red' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}

        <Grid item md={3} xs={12}>
          <Panel title="Success vs Failure">
            {isLoading ? <CircularProgress size={22} /> : hasHistory ? (
              <DonutChart centerLabel={analytics.total_queries.toString()} segments={[
                { label: 'Success', value: percent(analytics.successful_queries, analytics.total_queries), color: '#16a34a' },
                { label: 'Failure', value: percent(analytics.failed_queries, analytics.total_queries), color: '#ef4444' }
              ]} />
            ) : <EmptyState />}
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Cache Hit vs Miss">
            {isLoading ? <CircularProgress size={22} /> : hasHistory ? (
              <DonutChart centerLabel={analytics.total_queries.toString()} segments={[
                { label: 'Hit', value: percent(analytics.cache_hits, analytics.total_queries), color: '#2563eb' },
                { label: 'Miss', value: percent(analytics.cache_misses, analytics.total_queries), color: '#f59e0b' }
              ]} />
            ) : <EmptyState />}
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Rule vs LLM Generation">
            {isLoading ? <CircularProgress size={22} /> : hasHistory ? (
              <DonutChart centerLabel={analytics.total_queries.toString()} segments={[
                { label: 'Rule', value: percent(analytics.rule_generation_count, analytics.total_queries), color: '#0891b2' },
                { label: 'LLM', value: percent(analytics.llm_generation_count, analytics.total_queries), color: '#7c3aed' }
              ]} />
            ) : <EmptyState />}
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Query Volume Over Time">
            {isLoading ? <CircularProgress size={22} /> : volumeData.length > 0 ? (
              <LineChart color="#7c3aed" data={volumeData} labels={volumeLabels} />
            ) : <EmptyState />}
          </Panel>
        </Grid>

        <Grid item xs={12}>
          <Panel title="Recent Queries">
            {isLoading ? <CircularProgress size={22} /> : (
              <DataTable columns={['Natural Language Query', 'Generation Mode', 'Validation Status', 'Cache Status', 'Execution Time', 'Timestamp']} rows={recentRows.length > 0 ? recentRows : [['No query history records yet', '-', '-', '-', '-', '-']]} />
            )}
          </Panel>
        </Grid>
      </Grid>
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

function EmptyState() {
  return (
    <Typography color="text.secondary" variant="body2">
      No query history records available yet.
    </Typography>
  );
}
