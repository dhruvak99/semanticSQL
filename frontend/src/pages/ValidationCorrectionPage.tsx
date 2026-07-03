import { useEffect, useMemo, useState } from 'react';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import SecurityIcon from '@mui/icons-material/Security';
import StorageIcon from '@mui/icons-material/Storage';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { Alert, CircularProgress, Grid, Typography } from '@mui/material';
import { getValidationAnalytics, type ValidationAnalyticsResponse } from '../api/history';
import { DataTable, DonutChart, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

const emptyAnalytics: ValidationAnalyticsResponse = {
  total_validated_queries: 0,
  valid_queries: 0,
  invalid_queries: 0,
  validation_success_rate: 0,
  schema_mismatch_count: 0,
  cache_hit_count: 0,
  cache_miss_count: 0,
  validation_logs: [],
  recent_failures: []
};

export function ValidationCorrectionPage() {
  const [analytics, setAnalytics] = useState<ValidationAnalyticsResponse>(emptyAnalytics);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setIsLoading(true);
        setError(null);
        setAnalytics(await getValidationAnalytics());
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : 'Failed to load validation analytics');
      } finally {
        setIsLoading(false);
      }
    }

    void loadAnalytics();
  }, []);

  const hasHistory = analytics.total_validated_queries > 0;
  const otherValidationFailures = Math.max(analytics.invalid_queries - analytics.schema_mismatch_count, 0);
  const validationLogRows = useMemo(() => analytics.validation_logs.map((record) => [
    record.natural_language_query,
    previewSql(record.generated_sql),
    <StatusBadge label={record.validation_status} tone={record.validation_status.toLowerCase() === 'valid' ? 'green' : 'red'} />,
    <StatusBadge label={record.cache_status} tone={record.cache_status.toLowerCase() === 'hit' ? 'green' : 'red'} />,
    record.generation_mode,
    formatTimestamp(record.created_at)
  ]), [analytics.validation_logs]);
  const failureRows = useMemo(() => analytics.recent_failures.map((record) => [
    record.natural_language_query,
    previewSql(record.generated_sql),
    <StatusBadge label={record.failure_type} tone={record.failure_type === 'Schema Mismatch' ? 'red' : 'orange'} />,
    formatTimestamp(record.created_at)
  ]), [analytics.recent_failures]);

  return (
    <>
      <PageHeader title="Validation & Correction" description="Review real SQL validation outcomes, schema mismatch failures, and validation logs from query history." />
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}
      <Grid container spacing={2.5}>
        {[
          { label: 'Total Validated Queries', value: analytics.total_validated_queries.toLocaleString(), icon: SecurityIcon, trend: 'From query history', tone: 'green' },
          { label: 'Valid Queries', value: analytics.valid_queries.toLocaleString(), icon: CheckCircleOutlineIcon, trend: 'Validation status: valid', tone: 'green' },
          { label: 'Invalid Queries', value: analytics.invalid_queries.toLocaleString(), icon: ErrorOutlineIcon, trend: 'Validation status: invalid', trendDirection: 'down', tone: 'red' },
          { label: 'Validation Success Rate', value: `${analytics.validation_success_rate.toFixed(1)}%`, icon: CheckCircleOutlineIcon, trend: 'Valid / total', tone: 'blue' },
          { label: 'Schema Mismatch Count', value: analytics.schema_mismatch_count.toLocaleString(), icon: WarningAmberIcon, trend: 'SCHEMA_MISMATCH records', trendDirection: 'down', tone: 'orange' },
          { label: 'Cache Hits vs Misses', value: `${analytics.cache_hit_count}/${analytics.cache_miss_count}`, icon: StorageIcon, trend: 'Hit / miss', tone: 'purple' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}

        <Grid item md={6} xs={12}>
          <Panel title="Validation Results Breakdown">
            {isLoading ? <CircularProgress size={22} /> : hasHistory ? (
              <DonutChart centerLabel={analytics.total_validated_queries.toString()} segments={[
                { label: 'Valid', value: percent(analytics.valid_queries, analytics.total_validated_queries), color: '#16a34a' },
                { label: 'Invalid', value: percent(analytics.invalid_queries, analytics.total_validated_queries), color: '#ef4444' }
              ]} />
            ) : <EmptyState />}
          </Panel>
        </Grid>

        <Grid item md={6} xs={12}>
          <Panel title="Schema Mismatch Analysis">
            {isLoading ? <CircularProgress size={22} /> : hasHistory ? (
              <DonutChart centerLabel={analytics.invalid_queries.toString()} segments={[
                { label: 'Schema Mismatch', value: percent(analytics.schema_mismatch_count, Math.max(analytics.invalid_queries, 1)), color: '#ef4444' },
                { label: 'Validation Failure', value: percent(otherValidationFailures, Math.max(analytics.invalid_queries, 1)), color: '#f59e0b' }
              ]} />
            ) : <EmptyState />}
          </Panel>
        </Grid>

        <Grid item md={7} xs={12}>
          <Panel title="Validation Log">
            {isLoading ? <CircularProgress size={22} /> : (
              <DataTable columns={['Natural Language Query', 'Generated SQL', 'Validation Status', 'Cache Status', 'Generation Mode', 'Timestamp']} rows={validationLogRows.length > 0 ? validationLogRows : [['No validation records yet', '-', '-', '-', '-', '-']]} />
            )}
          </Panel>
        </Grid>

        <Grid item md={5} xs={12}>
          <Panel title="Recent Validation Failures">
            {isLoading ? <CircularProgress size={22} /> : (
              <DataTable columns={['Query', 'Generated SQL', 'Failure Type', 'Timestamp']} rows={failureRows.length > 0 ? failureRows : [['No validation failures yet', '-', '-', '-']]} />
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

function previewSql(sql: string) {
  return sql.length > 72 ? `${sql.slice(0, 72)}...` : sql;
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function EmptyState() {
  return (
    <Typography color="text.secondary" variant="body2">
      No validation records available yet.
    </Typography>
  );
}
