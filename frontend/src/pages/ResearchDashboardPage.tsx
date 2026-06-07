import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import MemoryIcon from '@mui/icons-material/Memory';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { Grid, Stack, Typography } from '@mui/material';
import { BarChart, DataTable, DonutChart, LineChart, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function ResearchDashboardPage() {
  return (
    <>
      <PageHeader title="Research Dashboard" description="Evaluate cache impact, latency reductions, LLM calls saved, and model-assisted performance gains." />
      <Grid container spacing={2.5}>
        {[
          { label: 'Total Queries (Test Set)', value: '2,560', icon: QueryStatsIcon, trend: '18.7% vs last 7 days', tone: 'blue' },
          { label: 'Cache Hit Rate', value: '87.3%', icon: StorageIcon, trend: '12.5% vs last 7 days', tone: 'green' },
          { label: 'Avg Latency Reduction', value: '73.6%', icon: SpeedIcon, trend: '3.2% variance', trendDirection: 'down', tone: 'purple' },
          { label: 'LLM Calls Saved', value: '2,241', icon: MemoryIcon, trend: '21.3% vs last 7 days', tone: 'orange' },
          { label: 'Correction Accuracy', value: '96.8%', icon: TrendingUpIcon, trend: '2.1% vs last 7 days', tone: 'purple' },
          { label: 'Execution Success', value: '98.1%', icon: CheckCircleOutlineIcon, trend: '1.4% vs last 7 days', tone: 'cyan' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}
        <Grid item md={5} xs={12}>
          <Panel title="Cache vs No Cache Comparison">
            <BarChart data={[{ label: 'Avg latency saved', value: 73.6, color: '#7c3aed' }, { label: 'P90 latency saved', value: 74.6, color: '#7c3aed' }, { label: 'Execution time saved', value: 75, color: '#16a34a' }, { label: 'LLM calls saved', value: 87.5, color: '#f59e0b' }]} max={100} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Latency Comparison">
            <LineChart color="#7c3aed" data={[0.05, 0.14, 0.42, 0.38, 0.16, 0.08]} secondaryColor="#94a3b8" secondaryData={[0.2, 0.4, 1.6, 4.8, 9.1, 1.4]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Performance Improvement Charts">
            <DonutChart centerLabel="0.82" segments={[{ label: 'High', value: 45.2, color: '#7c3aed' }, { label: 'Good', value: 34.1, color: '#2563eb' }, { label: 'Medium', value: 14.3, color: '#16a34a' }, { label: 'Low', value: 6.4, color: '#ef4444' }]} />
          </Panel>
        </Grid>
        <Grid item md={5} xs={12}>
          <Panel title="Query Type Performance">
            <DataTable columns={['Type', 'Queries', 'Hit Rate', 'Latency w/ Cache', 'Improvement']} rows={[
              ['SELECT', '1,845', '89.1%', '0.342s', <StatusBadge label="-77.0%" />],
              ['INSERT', '186', '82.3%', '0.512s', <StatusBadge label="-72.9%" />],
              ['UPDATE', '142', '84.5%', '0.621s', <StatusBadge label="-70.5%" />],
              ['DDL', '68', '75.0%', '0.712s', <StatusBadge label="-75.2%" />]
            ]} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Correction Accuracy Over Time">
            <LineChart color="#7c3aed" data={[89, 94, 94, 97, 97, 97, 98]} height={190} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="LLM Calls Saved">
            <Stack spacing={1.5}>
              <Typography variant="h3">2,241</Typography>
              <Typography color="text.secondary" variant="body2">Requests served from semantic cache instead of direct model generation.</Typography>
              <StatusBadge label="87.5% reduction" tone="green" />
            </Stack>
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
