import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import SecurityIcon from '@mui/icons-material/Security';
import { Grid, Stack, Typography } from '@mui/material';
import { DataTable, DonutChart, LineChart, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function ValidationCorrectionPage() {
  return (
    <>
      <PageHeader title="Validation & Correction" description="Track SQL validation logs, correction history, error categories, and correction success rates." />
      <Grid container spacing={2.5}>
        {[
          { label: 'Total Validated', value: '1,245', icon: SecurityIcon, trend: '18.4% vs last 7 days', tone: 'green' },
          { label: 'Valid Queries', value: '1,086', icon: CheckCircleOutlineIcon, trend: '12.6% vs last 7 days', tone: 'green' },
          { label: 'Queries with Errors', value: '159', icon: ErrorOutlineIcon, trend: '5.9% vs last 7 days', trendDirection: 'down', tone: 'red' },
          { label: 'Auto Corrections', value: '128', icon: AutoFixHighIcon, trend: '16.7% vs last 7 days', tone: 'blue' },
          { label: 'LLM Corrections', value: '97', icon: AutoFixHighIcon, trend: '21.2% vs last 7 days', tone: 'purple' },
          { label: 'Success Rate', value: '96.8%', icon: CheckCircleOutlineIcon, trend: '2.3% vs last 7 days', tone: 'orange' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}
        <Grid item xs={12}>
          <Panel title="SQL Validation & Correction Pipeline">
            <Grid container spacing={2}>
              {['Query Received', 'SQL Generated', 'Syntax Validation', 'Schema Validation', 'Auto Correction', 'LLM Correction', 'Validated SQL'].map((step, index) => (
                <Grid item key={step} md={12 / 7} sm={4} xs={12}>
                  <Stack spacing={1} sx={{ alignItems: 'center', textAlign: 'center' }}>
                    <StatusBadge label={`${index + 1}`} tone={index > 4 ? 'green' : 'blue'} />
                    <Typography fontWeight={800} variant="body2">{step}</Typography>
                    <Typography color="text.secondary" variant="caption">Enterprise validation stage</Typography>
                  </Stack>
                </Grid>
              ))}
            </Grid>
          </Panel>
        </Grid>
        <Grid item md={6} xs={12}>
          <Panel title="Validation Logs">
            <DataTable columns={['Query Preview', 'Status', 'Errors', 'Corrections', 'Time']} rows={[
              ['Show employees earning more than 60000', <StatusBadge label="Success" />, '1', <StatusBadge label="1 Auto" tone="orange" />, '11:24:17 AM'],
              ['List all departmnts', <StatusBadge label="Success" />, '2', <StatusBadge label="2 Auto" tone="orange" />, '11:23:45 AM'],
              ['Delete all records from old_logs', <StatusBadge label="Failed" tone="red" />, '3', '0', '11:12:07 AM']
            ]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Correction History">
            <DonutChart centerLabel="225" segments={[{ label: 'Auto', value: 56.9, color: '#16a34a' }, { label: 'LLM', value: 43.1, color: '#7c3aed' }]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Error Categories">
            <DonutChart segments={[{ label: 'Column Not Found', value: 30.2, color: '#7c3aed' }, { label: 'Syntax Error', value: 18.2, color: '#f59e0b' }, { label: 'Table Not Found', value: 22, color: '#2563eb' }, { label: 'Ambiguous Column', value: 13.2, color: '#ef4444' }, { label: 'Other', value: 16.4, color: '#94a3b8' }]} />
          </Panel>
        </Grid>
        <Grid item md={8} xs={12}>
          <Panel title="Correction Details">
            <DataTable columns={['Stage', 'Original SQL', 'Correction Applied', 'Corrected SQL', 'Method']} rows={[
              ['Schema Validation', 'SELECT name, salary FROM employees', "Table 'employees' not found", 'SELECT name, salary FROM employees', <StatusBadge label="Auto Fuzzy" />],
              ['Syntax Validation', 'SELECT name, salary WHERE salary > 50000', 'Missing FROM clause', 'SELECT name, salary FROM employees WHERE salary > 50000', <StatusBadge label="LLM" tone="purple" />],
              ['Schema Validation', 'AVG(salary) FROM employes', 'employes → employees', 'AVG(salary) FROM employees', <StatusBadge label="Auto Fuzzy" />]
            ]} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Success Rate Metrics">
            <LineChart color="#16a34a" data={[77, 85, 88, 90, 91, 92, 94]} height={180} />
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
