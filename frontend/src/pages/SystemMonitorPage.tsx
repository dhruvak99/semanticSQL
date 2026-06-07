import ApiIcon from '@mui/icons-material/Api';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import DnsIcon from '@mui/icons-material/Dns';
import MemoryIcon from '@mui/icons-material/Memory';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import { Grid, Stack, Typography } from '@mui/material';
import { DataTable, LineChart, MetricProgress, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function SystemMonitorPage() {
  return (
    <>
      <PageHeader title="System Monitor" description="Real-time service health, CPU, memory, Redis, database, and API performance metrics." />
      <Grid container spacing={2.5}>
        {[
          { label: 'Overall Status', value: 'Healthy', icon: CheckCircleOutlineIcon, helper: 'All systems operational', tone: 'green' },
          { label: 'Uptime', value: '15d 7h', icon: SpeedIcon, helper: '100% availability', tone: 'blue' },
          { label: 'Avg Response', value: '0.237 sec', icon: ApiIcon, trend: '12.4% vs last 7 days', tone: 'purple' },
          { label: 'Connections', value: '128', icon: DnsIcon, trend: '8.2% vs last 7 days', tone: 'blue' },
          { label: 'Requests (7D)', value: '1.24M', icon: StorageIcon, trend: '18.7% vs last 7 days', tone: 'cyan' },
          { label: 'Error Rate', value: '0.12%', icon: MemoryIcon, trend: '0.03% vs last 7 days', trendDirection: 'down', tone: 'red' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}
        <Grid item md={5} xs={12}>
          <Panel title="CPU / Memory Resource Usage">
            <LineChart data={[52, 58, 62, 55, 60, 54, 62]} secondaryColor="#16a34a" secondaryData={[34, 39, 38, 37, 38, 37, 40]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="System Health">
            <Stack spacing={1.5}>
              {['MySQL Database', 'Redis Cache', 'LLM Service (GPT-4o)', 'API Service', 'Web Dashboard'].map((service) => (
                <Stack direction="row" key={service} sx={{ justifyContent: 'space-between' }}>
                  <Typography variant="body2">{service}</Typography>
                  <StatusBadge label="Healthy" />
                </Stack>
              ))}
            </Stack>
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Memory / Infrastructure Overview">
            <Grid container spacing={2}>
              <Grid item xs={6}><MetricProgress label="CPU" value={42} detail="16 cores" tone="blue" /></Grid>
              <Grid item xs={6}><MetricProgress label="Memory" value={58} detail="18.6 / 32 GB" tone="green" /></Grid>
              <Grid item xs={6}><MetricProgress label="Disk" value={28} detail="278 GB / 1 TB" tone="purple" /></Grid>
              <Grid item xs={6}><MetricProgress label="Network" value={31} detail="285 MB/s in" tone="orange" /></Grid>
            </Grid>
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}><Panel title="Redis Metrics"><MetricProgress label="Hit Rate" value={87} detail="1,842 ops/sec" tone="green" /><MetricProgress label="Memory Used" value={64} detail="2.41 GB" tone="blue" /></Panel></Grid>
        <Grid item md={3} xs={12}><Panel title="Database Metrics"><MetricProgress label="QPS" value={72} detail="145.2 queries/sec" tone="blue" /><MetricProgress label="Buffer Pool" value={99} detail="12.4 / 16 GB" tone="green" /></Panel></Grid>
        <Grid item md={3} xs={12}><Panel title="API Metrics"><MetricProgress label="Success Rate" value={99} detail="1.24M requests" tone="orange" /><MetricProgress label="Active Requests" value={23} detail="23 currently active" tone="gray" /></Panel></Grid>
        <Grid item md={3} xs={12}><Panel title="Model Service Metrics"><MetricProgress label="Success Rate" value={99} detail="12,541 requests" tone="purple" /><MetricProgress label="Token Usage" value={76} detail="18.6M tokens" tone="purple" /></Panel></Grid>
        <Grid item md={7} xs={12}>
          <Panel title="Network Traffic">
            <LineChart color="#16a34a" data={[380, 320, 490, 340, 480, 330, 470]} secondaryData={[220, 260, 210, 250, 230, 310, 260]} />
          </Panel>
        </Grid>
        <Grid item md={5} xs={12}>
          <Panel title="Active Alerts">
            <DataTable columns={['Severity', 'Alert', 'Service', 'Time']} rows={[[<StatusBadge label="Warning" tone="orange" />, 'High memory usage', 'Redis Cache', '2m ago'], [<StatusBadge label="Critical" tone="red" />, 'Slow query detected', 'MySQL Database', '5m ago'], [<StatusBadge label="Warning" tone="orange" />, 'High response time', 'LLM Service', '12m ago']]} />
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
