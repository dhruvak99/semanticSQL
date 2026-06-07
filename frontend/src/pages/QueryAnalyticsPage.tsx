import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import TimerIcon from '@mui/icons-material/Timer';
import { Button, Grid } from '@mui/material';
import { BarChart, DataTable, DonutChart, Heatmap, LineChart, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function QueryAnalyticsPage() {
  return (
    <>
      <PageHeader title="Query Analytics" description="Analyze query performance, volume trends, query types, slow queries, and workload hotspots." />
      <Grid container spacing={2.5}>
        {[
          { label: 'Total Queries', value: '1,245', icon: QueryStatsIcon, trend: '18.4% vs last 7 days', tone: 'blue' },
          { label: 'Avg Execution Time', value: '0.421 sec', icon: SpeedIcon, trend: '23.1% faster', tone: 'blue' },
          { label: '90th Percentile', value: '1.842 sec', icon: TimerIcon, trend: '19.7% faster', tone: 'purple' },
          { label: 'Slow Queries', value: '24', icon: ErrorOutlineIcon, trend: '14.3% vs last 7 days', trendDirection: 'down', tone: 'red' },
          { label: 'Rows Returned', value: '125.8K', icon: StorageIcon, trend: '22.6% vs last 7 days', tone: 'green' },
          { label: 'Errors', value: '18', icon: ErrorOutlineIcon, trend: '5.9% vs last 7 days', trendDirection: 'down', tone: 'red' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}
        <Grid item md={5} xs={12}>
          <Panel action={<Button variant="outlined">Daily</Button>} title="Query Volume Trends">
            <LineChart color="#7c3aed" data={[184, 312, 302, 312, 502, 366, 536]} labels={['May 15', 'May 16', 'May 17', 'May 18', 'May 19', 'May 20', 'May 21']} />
          </Panel>
        </Grid>
        <Grid item md={3.5} xs={12}>
          <Panel title="Query Type Distribution">
            <DonutChart segments={[{ label: 'SELECT', value: 72.1, color: '#2563eb' }, { label: 'INSERT', value: 10.3, color: '#16a34a' }, { label: 'UPDATE', value: 8.7, color: '#f59e0b' }, { label: 'DELETE', value: 5.4, color: '#7c3aed' }, { label: 'DDL', value: 3.5, color: '#94a3b8' }]} />
          </Panel>
        </Grid>
        <Grid item md={3.5} xs={12}>
          <Panel title="Execution Time Distribution">
            <DonutChart segments={[{ label: '<= 100ms', value: 31.2, color: '#16a34a' }, { label: '100-500ms', value: 41.7, color: '#2563eb' }, { label: '500ms-1s', value: 15.8, color: '#f59e0b' }, { label: '1s-2s', value: 7.6, color: '#7c3aed' }, { label: '> 2s', value: 3.7, color: '#ef4444' }]} />
          </Panel>
        </Grid>
        <Grid item md={3.5} xs={12}>
          <Panel title="Most Queried Tables">
            <DataTable columns={['#', 'Table', 'Count', '%']} rows={[['1', 'employees', '523', '28.4%'], ['2', 'departments', '312', '16.9%'], ['3', 'salaries', '198', '10.8%'], ['4', 'projects', '156', '8.5%']]} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Average Execution Time by Query Type">
            <BarChart data={[{ label: 'SELECT', value: 0.432, color: '#7c3aed' }, { label: 'INSERT', value: 0.312, color: '#16a34a' }, { label: 'UPDATE', value: 0.584, color: '#f59e0b' }, { label: 'DELETE', value: 0.671, color: '#7c3aed' }, { label: 'DDL', value: 1.231, color: '#94a3b8' }]} max={1.5} />
          </Panel>
        </Grid>
        <Grid item md={4.5} xs={12}>
          <Panel title="Slow Query Analysis">
            <DataTable columns={['#', 'Query Preview', 'Execution Time', 'Count']} rows={[
              ['1', 'SELECT * FROM employees e JOIN salaries s ...', <StatusBadge label="4.812 sec" tone="red" />, '23'],
              ['2', 'SELECT d.name, AVG(s.salary) FROM ...', <StatusBadge label="3.245 sec" tone="red" />, '17'],
              ['3', 'SELECT * FROM projects p LEFT JOIN ...', <StatusBadge label="2.983 sec" tone="orange" />, '15']
            ]} />
          </Panel>
        </Grid>
        <Grid item md={6} xs={12}>
          <Panel title="Query Trends (7-Day Moving Average)">
            <LineChart color="#7c3aed" data={[238, 324, 351, 374, 421, 401, 482]} secondaryColor="#16a34a" secondaryData={[198, 256, 268, 292, 342, 322, 398]} />
          </Panel>
        </Grid>
        <Grid item md={6} xs={12}>
          <Panel title="Query Heatmap by Hour of Day">
            <Heatmap columns={['12A', '3A', '6A', '9A', '12P', '3P', '6P', '9P']} rows={['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']} />
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
