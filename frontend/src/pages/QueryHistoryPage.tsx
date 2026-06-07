import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import HistoryIcon from '@mui/icons-material/History';
import SearchIcon from '@mui/icons-material/Search';
import SpeedIcon from '@mui/icons-material/Speed';
import StorageIcon from '@mui/icons-material/Storage';
import { Button, Grid, InputAdornment, Stack, TextField } from '@mui/material';
import { CodeBlock, DataTable, FilterBar, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function QueryHistoryPage() {
  return (
    <>
      <PageHeader title="Query History" description="Search and audit natural language prompts, generated SQL, execution metadata, and cache outcomes." />
      <Grid container spacing={2.5}>
        {[
          { label: 'Total Queries', value: '1,245', icon: HistoryIcon, trend: '18.4% vs last 7 days', tone: 'purple' },
          { label: 'Successful Queries', value: '1,118', icon: CheckCircleOutlineIcon, trend: '12.6% vs last 7 days', tone: 'green' },
          { label: 'Avg Execution Time', value: '0.421 sec', icon: SpeedIcon, trend: '23.1% faster', tone: 'orange' },
          { label: 'Cache Hit Rate', value: '87.3%', icon: StorageIcon, trend: '12.6% vs last 7 days', tone: 'blue' },
          { label: 'Failed Queries', value: '127', icon: ErrorOutlineIcon, trend: '5.9% vs last 7 days', trendDirection: 'down', tone: 'red' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2.4} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} trendDirection={stat.trendDirection as never} />
          </Grid>
        ))}
        <Grid item xs={12}>
          <FilterBar items={['All Users', 'All Status', 'All Cache Status', 'All Query Types']} />
        </Grid>
        <Grid item md={8.5} xs={12}>
          <Panel
            action={<Button variant="outlined">Export CSV</Button>}
            title="Searchable History Table"
          >
            <TextField
              fullWidth
              InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> }}
              placeholder="Search queries, SQL, users, or keywords..."
              size="small"
              sx={{ mb: 2 }}
            />
            <DataTable columns={['#', 'Natural Language Query', 'Generated SQL Preview', 'Status', 'Cache', 'Execution', 'User', 'Time']} rows={[
              ['1', 'Show all employees earning more than 60000', 'SELECT * FROM employees WHERE salary > 60000', <StatusBadge label="Success" />, <StatusBadge label="Hit" />, '0.245 sec', 'Admin', '11:24 AM'],
              ['2', 'List all departments', 'SELECT * FROM departments', <StatusBadge label="Success" />, <StatusBadge label="Hit" />, '0.123 sec', 'analyst', '11:20 AM'],
              ['3', 'Count employees in each department', 'SELECT d.name, COUNT(e.id) FROM ...', <StatusBadge label="Success" />, <StatusBadge label="Miss" tone="red" />, '0.512 sec', 'analyst', '11:18 AM'],
              ['4', 'Show total salary by departmnt', 'SELECT dept, SUM(salary) FROM ...', <StatusBadge label="Failed" tone="red" />, <StatusBadge label="Miss" tone="red" />, '-', 'hr_user', '11:02 AM']
            ]} />
          </Panel>
        </Grid>
        <Grid item md={3.5} xs={12}>
          <Stack spacing={2.5}>
            <Panel title="Execution Metadata">
              <DataTable columns={['Field', 'Value']} rows={[['Query ID', 'QRY-2024-05-21-001245'], ['User', 'Admin'], ['Status', <StatusBadge label="Success" />], ['Rows Returned', '18'], ['Model Used', 'gpt-4o'], ['IP Address', '192.168.1.101']]} />
            </Panel>
            <Panel title="SQL Preview">
              <CodeBlock code={`SELECT * FROM employees\nWHERE salary > 60000\nORDER BY salary DESC;`} />
            </Panel>
          </Stack>
        </Grid>
      </Grid>
    </>
  );
}
