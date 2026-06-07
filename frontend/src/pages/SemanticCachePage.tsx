import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import HubIcon from '@mui/icons-material/Hub';
import StorageIcon from '@mui/icons-material/Storage';
import { Button, Grid, Stack, Typography } from '@mui/material';
import { BarChart, DataTable, DonutChart, LineChart, MetricProgress, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function SemanticCachePage() {
  return (
    <>
      <PageHeader title="Semantic Cache" description="View semantic cache performance, similar query matches, Redis statistics, and saved executions." />
      <Grid container spacing={2.5}>
        {[
          { label: 'Cache Hit Rate', value: '87.3%', icon: CheckCircleOutlineIcon, trend: '12.6% vs last 7 days', tone: 'green' },
          { label: 'Cache Hits', value: '1,086', icon: StorageIcon, trend: '15.6% vs last 7 days', tone: 'green' },
          { label: 'Cache Misses', value: '159', icon: HighlightOffIcon, trend: '28.1% vs last 7 days', trendDirection: 'down', tone: 'red' },
          { label: 'Total Entries', value: '2,341', icon: HubIcon, trend: '312 new entries', tone: 'blue' },
          { label: 'Avg Similarity', value: '0.93', icon: CheckCircleOutlineIcon, trend: '0.04 vs last 7 days', tone: 'purple' },
          { label: 'Time Saved', value: '14.2 hrs', icon: AccessTimeIcon, trend: '2.8 hrs vs last 7 days', tone: 'orange' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}
        <Grid item md={6} xs={12}>
          <Panel action={<Button variant="outlined">Daily</Button>} title="Cache Hit/Miss Cards Over Time">
            <LineChart color="#16a34a" data={[420, 510, 580, 640, 720, 850, 812]} labels={['May 15', 'May 16', 'May 17', 'May 18', 'May 19', 'May 20', 'May 21']} secondaryColor="#ef4444" secondaryData={[95, 142, 158, 184, 176, 232, 334]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Similarity Score Chart">
            <DonutChart centerLabel="0.93" segments={[{ label: '0.90-1.00', value: 69.2, color: '#16a34a' }, { label: '0.80-0.90', value: 21.1, color: '#f59e0b' }, { label: '0.70-0.80', value: 6.8, color: '#ef4444' }, { label: '< 0.70', value: 2.9, color: '#94a3b8' }]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Redis Statistics">
            <Stack spacing={2}>
              <MetricProgress label="Memory Usage" value={64} detail="128.7 MB used" tone="blue" />
              <MetricProgress label="Keyspace Hits" value={87} detail="1,086 successful lookups" tone="green" />
              <MetricProgress label="Keyspace Misses" value={13} detail="159 misses" tone="red" />
              <Typography variant="body2">Policy: <strong>LRU</strong> · Retrieval: <strong>12.4 ms</strong></Typography>
            </Stack>
          </Panel>
        </Grid>
        <Grid item md={6} xs={12}>
          <Panel action={<Button variant="outlined">View All</Button>} title="Top Cached Queries">
            <DataTable columns={['#', 'Query', 'Use Count', 'Hit Rate', 'Last Used']} rows={[
              ['1', 'Show all employees earning more than 50000', '23', '95.8%', '2 min ago'],
              ['2', 'List all departments', '18', '94.7%', '5 min ago'],
              ['3', 'Count employees in each department', '15', '93.3%', '8 min ago'],
              ['4', 'Show employees in the Finance department', '13', '92.3%', '12 min ago']
            ]} />
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
