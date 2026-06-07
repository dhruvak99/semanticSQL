import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import DataObjectIcon from '@mui/icons-material/DataObject';
import MemoryIcon from '@mui/icons-material/Memory';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import { Button, Grid, Stack, Typography } from '@mui/material';
import { BarChart, DataTable, DonutChart, LineChart, MetricProgress, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function DashboardPage() {
  return (
    <>
      <PageHeader title="Dashboard" description="Overview of natural-language SQL activity, semantic cache efficiency, and platform health." />
      <Grid container spacing={2.5}>
        {[
          { label: 'Total Queries', value: '1,245', trend: '18.4% vs last 7 days', icon: ChatBubbleOutlineIcon, tone: 'blue' },
          { label: 'Cache Hit Rate', value: '87.3%', trend: '12.6% vs last 7 days', icon: StorageIcon, tone: 'green' },
          { label: 'Average Latency', value: '0.421 sec', trend: '23.1% faster', icon: SpeedIcon, tone: 'orange' },
          { label: 'LLM Calls Saved', value: '1,086', trend: '16.7% vs last 7 days', icon: MemoryIcon, tone: 'purple' },
          { label: 'Success Rate', value: '98.7%', trend: '2.2% vs last 7 days', icon: CheckCircleOutlineIcon, tone: 'green' },
          { label: 'Queries Executed', value: '1,245', trend: '18.4% vs last 7 days', icon: DataObjectIcon, tone: 'red' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} />
          </Grid>
        ))}
        <Grid item md={6} xs={12}>
          <Panel action={<Button variant="outlined">Daily</Button>} title="Query Volume Over Time">
            <LineChart data={[168, 274, 266, 271, 426, 316, 452]} labels={['May 15', 'May 16', 'May 17', 'May 18', 'May 19', 'May 20', 'May 21']} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Cache Hit Rate Chart">
            <DonutChart centerLabel="87.3%" segments={[{ label: 'Hits', value: 87.3, color: '#16a34a' }, { label: 'Misses', value: 12.7, color: '#ef4444' }]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="System Health Widgets">
            <Stack spacing={2}>
              {['MySQL Database', 'Redis Cache', 'LLM Service', 'Embedding Service', 'API Service'].map((service) => (
                <Stack direction="row" key={service} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="body2">{service}</Typography>
                  <StatusBadge label="Healthy" />
                </Stack>
              ))}
            </Stack>
          </Panel>
        </Grid>
        <Grid item md={7} xs={12}>
          <Panel action={<Button variant="outlined">View All</Button>} title="Recent Activity Table">
            <DataTable
              columns={['Query', 'Type', 'Status', 'Latency', 'Time', 'Cache']}
              rows={[
                ['Show employees earning > 50000', <StatusBadge label="SELECT" tone="blue" />, <StatusBadge label="Success" />, '0.142 sec', '2 min ago', <StatusBadge label="Hit" />],
                ['List all departments', <StatusBadge label="SELECT" tone="blue" />, <StatusBadge label="Success" />, '0.085 sec', '5 min ago', <StatusBadge label="Hit" />],
                ['Count employees in each dept', <StatusBadge label="SELECT" tone="blue" />, <StatusBadge label="Success" />, '0.126 sec', '8 min ago', <StatusBadge label="Miss" tone="red" />],
                ['Create project assignment table', <StatusBadge label="DDL" tone="purple" />, <StatusBadge label="Validated" />, '0.332 sec', '12 min ago', <StatusBadge label="Miss" tone="red" />]
              ]}
            />
          </Panel>
        </Grid>
        <Grid item md={2.5} xs={12}>
          <Panel title="Top Queried Tables">
            <BarChart data={[{ label: 'employees', value: 523 }, { label: 'departments', value: 312, color: '#16a34a' }, { label: 'salaries', value: 198, color: '#f59e0b' }, { label: 'projects', value: 156, color: '#7c3aed' }]} />
          </Panel>
        </Grid>
        <Grid item md={2.5} xs={12}>
          <Panel title="System Overview">
            <Stack spacing={2}>
              <MetricProgress label="Redis Memory" value={64} detail="128.7 MB used" tone="red" />
              <MetricProgress label="Connections" value={42} detail="24 active connections" tone="blue" />
              <MetricProgress label="Uptime" value={99} detail="30 days" tone="green" />
            </Stack>
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
