import { useEffect, useMemo, useState } from 'react';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import HubIcon from '@mui/icons-material/Hub';
import StorageIcon from '@mui/icons-material/Storage';
import { Button, Grid, Stack, Typography } from '@mui/material';
import { BarChart, DataTable, DonutChart, LineChart, MetricProgress, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';
import { getSemanticCacheMetrics, type SemanticCacheMetrics } from '../api/cache';

const emptyMetrics: SemanticCacheMetrics = {
  backend: 'memory',
  cache_hits: 0,
  cache_misses: 0,
  hit_rate: 0,
  average_similarity_score: 0,
  cache_entry_count: 0,
  top_cached_queries: []
};

export function SemanticCachePage() {
  const [metrics, setMetrics] = useState<SemanticCacheMetrics>(emptyMetrics);

  useEffect(() => {
    getSemanticCacheMetrics()
      .then(setMetrics)
      .catch(() => setMetrics(emptyMetrics));
  }, []);

  const totalLookups = metrics.cache_hits + metrics.cache_misses;
  const topCachedRows = useMemo(() => {
    if (metrics.top_cached_queries.length === 0) {
      return [['-', 'No cached queries yet', '0', '0.0000', '-']];
    }

    return metrics.top_cached_queries.map((entry, index) => [
      String(index + 1),
      entry.query,
      String(entry.hit_count),
      entry.last_similarity_score.toFixed(4),
      new Date(entry.timestamp).toLocaleString()
    ]);
  }, [metrics.top_cached_queries]);

  return (
    <>
      <PageHeader title="Semantic Cache" description="View semantic cache performance, similar query matches, Redis statistics, and saved executions." />
      <Grid container spacing={2.5}>
        {[
          { label: 'Cache Hit Rate', value: `${metrics.hit_rate.toFixed(1)}%`, icon: CheckCircleOutlineIcon, trend: `${totalLookups} lookups`, tone: 'green' },
          { label: 'Cache Hits', value: metrics.cache_hits.toLocaleString(), icon: StorageIcon, trend: 'Real cache hits', tone: 'green' },
          { label: 'Cache Misses', value: metrics.cache_misses.toLocaleString(), icon: HighlightOffIcon, trend: 'Real cache misses', trendDirection: 'down', tone: 'red' },
          { label: 'Total Entries', value: metrics.cache_entry_count.toLocaleString(), icon: HubIcon, trend: `${metrics.backend} backend`, tone: 'blue' },
          { label: 'Avg Similarity', value: metrics.average_similarity_score.toFixed(2), icon: CheckCircleOutlineIcon, trend: 'Across lookups', tone: 'purple' },
          { label: 'Time Saved', value: `${metrics.cache_hits}`, icon: AccessTimeIcon, trend: 'executions avoided', tone: 'orange' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}
        <Grid item md={6} xs={12}>
          <Panel action={<Button variant="outlined">Daily</Button>} title="Cache Hit/Miss Cards Over Time">
            <LineChart color="#16a34a" data={[0, 0, 0, metrics.cache_hits, metrics.cache_hits, metrics.cache_hits, metrics.cache_hits]} labels={['T-6', 'T-5', 'T-4', 'T-3', 'T-2', 'T-1', 'Now']} secondaryColor="#ef4444" secondaryData={[0, 0, 0, metrics.cache_misses, metrics.cache_misses, metrics.cache_misses, metrics.cache_misses]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Similarity Score Chart">
            <DonutChart centerLabel={metrics.average_similarity_score.toFixed(2)} segments={[{ label: 'Hits', value: metrics.cache_hits || 1, color: '#16a34a' }, { label: 'Misses', value: metrics.cache_misses || 1, color: '#ef4444' }]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Redis Statistics">
            <Stack spacing={2}>
              <MetricProgress label="Hit Rate" value={Math.round(metrics.hit_rate)} detail={`${metrics.cache_hits} successful lookups`} tone="green" />
              <MetricProgress label="Miss Rate" value={Math.round(100 - metrics.hit_rate)} detail={`${metrics.cache_misses} misses`} tone="red" />
              <Typography variant="body2">Backend: <strong>{metrics.backend}</strong> · Threshold: <strong>0.90</strong></Typography>
            </Stack>
          </Panel>
        </Grid>
        <Grid item md={6} xs={12}>
          <Panel action={<Button variant="outlined">View All</Button>} title="Top Cached Queries">
            <DataTable columns={['#', 'Query', 'Hit Count', 'Last Similarity', 'Last Used']} rows={topCachedRows} />
          </Panel>
        </Grid>
        <Grid item md={6} xs={12}>
          <Panel title="Similar Queries">
            <DataTable columns={['User Query', 'Matched Cached Query', 'Score', 'Hit Count']} rows={[
              ['Show employees with salary > 60000', 'Show employees earning more than 50000', <StatusBadge label="0.96" />, '23'],
              ['List workers with salary greater than 50000', 'Show employees earning more than 50000', <StatusBadge label="0.94" />, '18'],
              ['Employees earning above 50k', 'Show all employees earning more than 50000', <StatusBadge label="0.93" />, '11']
            ]} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Cache Growth">
            <LineChart data={[420, 880, 1260, 1520, 1880, 2040, 2341]} height={180} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Time Saved Metrics">
            <LineChart color="#7c3aed" data={[4.8, 7.4, 10.1, 12.9, 15.3, 15.7, 17.2]} height={180} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Cache Efficiency">
            <Stack spacing={2}>
              <Typography variant="h3">87.3%</Typography>
              <StatusBadge label="Excellent" />
              <BarChart data={[{ label: 'LLM calls avoided', value: 1086, color: '#16a34a' }, { label: 'New generations', value: 159, color: '#ef4444' }]} />
            </Stack>
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
