import AccountTreeIcon from '@mui/icons-material/AccountTree';
import CodeIcon from '@mui/icons-material/Code';
import HistoryIcon from '@mui/icons-material/History';
import RestoreIcon from '@mui/icons-material/Restore';
import SchemaIcon from '@mui/icons-material/Schema';
import TableChartIcon from '@mui/icons-material/TableChart';
import { Button, Grid, List, ListItemButton, ListItemText, Stack, TextField, Typography } from '@mui/material';
import { CodeBlock, DataTable, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function SchemaManagerPage() {
  return (
    <>
      <PageHeader title="Schema Manager" description="Manage database objects, DDL history, schema version tracking, changes, and rollback workflows." />
      <Grid container spacing={2.5}>
        {[
          { label: 'Total Tables', value: '24', icon: TableChartIcon, trend: '2 vs last 30 days', tone: 'blue' },
          { label: 'Views', value: '12', icon: SchemaIcon, trend: '1 vs last 30 days', tone: 'cyan' },
          { label: 'Stored Procedures', value: '8', icon: CodeIcon, helper: 'No change', tone: 'orange' },
          { label: 'Schema Version', value: 'v1.24.0', icon: AccountTreeIcon, helper: 'Current version', tone: 'purple' },
          { label: 'Last Updated', value: 'May 21', icon: HistoryIcon, helper: '11:24 AM', tone: 'green' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2.4} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} />
          </Grid>
        ))}
        <Grid item md={2.4} xs={12}>
          <Panel title="Database Objects">
            <TextField fullWidth placeholder="Search objects..." size="small" sx={{ mb: 2 }} />
            <List dense>
              {['employees', 'departments', 'salaries', 'projects', 'attendance', 'users'].map((item, index) => (
                <ListItemButton key={item} selected={index === 0} sx={{ borderRadius: 1 }}>
                  <ListItemText primary={item} secondary={index === 0 ? 'Tables (24)' : 'Database object'} />
                </ListItemButton>
              ))}
            </List>
          </Panel>
        </Grid>
        <Grid item md={6.2} xs={12}>
          <Stack spacing={2.5}>
            <Panel action={<Button variant="outlined">Edit Table</Button>} title="Schema Changes">
              <Typography fontWeight={800} sx={{ mb: 1 }}>Table: employees</Typography>
              <DataTable columns={['#', 'Column Name', 'Data Type', 'Nullable', 'Key', 'Default', 'Comment']} rows={[
                ['1', 'employee_id', 'INT', 'NO', <StatusBadge label="PRI" tone="blue" />, 'NULL', 'Employee ID'],
                ['2', 'department_id', 'INT', 'YES', <StatusBadge label="MUL" tone="purple" />, 'NULL', 'Department ID'],
                ['3', 'name', 'VARCHAR(100)', 'NO', '', 'NULL', 'Employee Name'],
                ['4', 'email', 'VARCHAR(150)', 'YES', <StatusBadge label="UNI" tone="orange" />, 'NULL', 'Email Address'],
                ['5', 'salary', 'DECIMAL(12,2)', 'YES', '', 'NULL', 'Salary Amount']
              ]} />
            </Panel>
            <Panel title="DDL History">
              <DataTable columns={['Action', 'Object', 'Type', 'User', 'Time', 'Status']} rows={[
                ['ALTER TABLE', 'employees', 'TABLE', 'Admin', 'May 21, 11:24 AM', <StatusBadge label="Success" />],
                ['CREATE VIEW', 'vw_salary_analytics', 'VIEW', 'Admin', 'May 21, 10:15 AM', <StatusBadge label="Success" />],
                ['DROP INDEX', 'idx_old_salary', 'INDEX', 'Admin', 'May 20, 02:11 PM', <StatusBadge label="Success" />]
              ]} />
            </Panel>
          </Stack>
        </Grid>
        <Grid item md={3.4} xs={12}>
          <Stack spacing={2.5}>
            <Panel action={<Button startIcon={<CodeIcon />}>Generate DDL</Button>} title="Rollback Panel">
              <CodeBlock code={`CREATE TABLE employees (\n  employee_id INT NOT NULL AUTO_INCREMENT,\n  department_id INT,\n  name VARCHAR(100) NOT NULL,\n  email VARCHAR(150) UNIQUE,\n  salary DECIMAL(12,2),\n  PRIMARY KEY (employee_id)\n);`} />
              <Button fullWidth startIcon={<RestoreIcon />} sx={{ mt: 2 }} variant="outlined">Rollback to v1.23.0</Button>
            </Panel>
            <Panel title="Version Tracking">
              <DataTable columns={['Version', 'Time', 'Status']} rows={[['v1.24.0', 'May 21, 11:24 AM', <StatusBadge label="Current" />], ['v1.23.0', 'May 20, 04:32 PM', <StatusBadge label="Stable" tone="blue" />], ['v1.22.0', 'May 19, 11:09 AM', <StatusBadge label="Archived" tone="gray" />]]} />
            </Panel>
          </Stack>
        </Grid>
      </Grid>
    </>
  );
}
