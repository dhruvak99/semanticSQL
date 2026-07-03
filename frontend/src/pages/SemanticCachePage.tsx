import { useEffect, useMemo, useState } from 'react';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import HubIcon from '@mui/icons-material/Hub';
import RefreshIcon from '@mui/icons-material/Refresh';
import StorageIcon from '@mui/icons-material/Storage';
import { Alert, Button, CircularProgress, Grid, Stack, Typography } from '@mui/material';
import { getSemanticCacheMetrics, type SemanticCacheMetrics } from '../api/cache';
import { DataTable, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function SemanticCachePage() {
  const [metrics, setMetrics] = useState<SemanticCacheMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadMetrics() {
    try {
      setIsLoading(true);
      setError(null);
      setMetrics(await getSemanticCacheMetrics());
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Failed to load semantic cache metrics');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadMetrics();
  }, []);

  const topCachedRows = useMemo(() => metrics?.top_cached_queries.map((entry) => [
    entry.query,
    <Typography
      key={`${entry.query}-sql`}
      component="span"
      fontFamily="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
      variant="body2"
    >
      {entry.generated_sql}
    </Typography>,
    entry.hit_count.toLocaleString(),
    entry.last_similarity_score.toFixed(4),
    formatTimestamp(entry.timestamp)
  ]) ?? [], [metrics]);

  return (
    <>
      <PageHeader title="Semantic Cache" description="Inspect Redis-backed semantic cache performance, configuration, and cached query entries." />
      {error ? (
        <Alert
          action={<Button color="inherit" onClick={() => void loadMetrics()} size="small">Retry</Button>}
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
            Loading semantic cache metrics...
          </Typography>
        </Stack>
      ) : metrics ? (
        <Grid container spacing={2.5}>
          {[
            { label: 'Cache Hit Rate', value: `${metrics.hit_rate.toFixed(1)}%`, icon: CheckCircleOutlineIcon, trend: `${metrics.cache_hits + metrics.cache_misses} lookups`, tone: 'green' },
            { label: 'Cache Hits', value: metrics.cache_hits.toLocaleString(), icon: StorageIcon, trend: 'Successful semantic matches', tone: 'green' },
            { label: 'Cache Misses', value: metrics.cache_misses.toLocaleString(), icon: HighlightOffIcon, trend: 'Queries requiring generation', trendDirection: 'down', tone: 'red' },
            { label: 'Total Cache Entries', value: metrics.cache_entry_count.toLocaleString(), icon: HubIcon, trend: `${formatBackend(metrics.backend)} backend`, tone: 'blue' },
            { label: 'Average Similarity Score', value: metrics.average_similarity_score.toFixed(4), icon: CheckCircleOutlineIcon, trend: 'Across cache lookups', tone: 'purple' },
            { label: 'Executions Avoided', value: metrics.cache_hits.toLocaleString(), icon: AccessTimeIcon, trend: 'SQL generations and executions skipped', tone: 'orange' }
          ].map((stat) => (
            <Grid item key={stat.label} md={2} sm={6} xs={12}>
              <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
            </Grid>
          ))}

          <Grid item md={4} xs={12}>
            <Panel title="Cache Configuration">
              <DataTable columns={['Setting', 'Value']} rows={[
                ['Backend', <StatusBadge key="backend" label={formatBackend(metrics.backend)} tone={metrics.backend === 'redis' ? 'green' : 'orange'} />],
                ['Similarity Threshold', metrics.similarity_threshold.toFixed(2)],
                ['Total Entries', metrics.cache_entry_count.toLocaleString()]
              ]} />
            </Panel>
          </Grid>

          <Grid item md={8} xs={12}>
            <Panel
              action={<Button onClick={() => void loadMetrics()} startIcon={<RefreshIcon />} variant="outlined">Refresh</Button>}
              title="Top Cached Queries"
            >
              {metrics.cache_entry_count === 0 ? (
                <Typography color="text.secondary" variant="body2">
                  No semantic cache entries available yet.
                  Run queries from Query Interface to populate the cache.
                </Typography>
              ) : (
                <DataTable
                  columns={['Natural Language Query', 'Generated SQL', 'Hit Count', 'Last Similarity Score', 'Last Used Timestamp']}
                  rows={topCachedRows}
                />
              )}
            </Panel>
          </Grid>
        </Grid>
      ) : null}
    </>
  );
}

function formatBackend(backend: SemanticCacheMetrics['backend']) {
  return backend === 'redis' ? 'Redis' : 'InMemory';
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
