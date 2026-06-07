import AddIcon from '@mui/icons-material/Add';
import DownloadIcon from '@mui/icons-material/Download';
import RefreshIcon from '@mui/icons-material/Refresh';
import TableChartIcon from '@mui/icons-material/TableChart';
import { Button, Grid, List, ListItemButton, ListItemIcon, ListItemText, Stack, TextField, Typography } from '@mui/material';
import { DataTable, Panel, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function DatabaseExplorerPage() {
  return (
    <>
      <PageHeader title="Database Explorer" description="Explore database schemas, tables, columns, relationships, indexes, and sample data." />
      <Stack direction="row" spacing={1.5} sx={{ justifyContent: 'flex-end', mb: 2 }}>
        <Button startIcon={<RefreshIcon />} variant="outlined">Refresh Schema</Button>
        <Button startIcon={<DownloadIcon />} variant="outlined">Export Schema</Button>
      </Stack>
      <Grid container spacing={2.5}>
        <Grid item md={2.4} xs={12}>
          <Panel action={<Button startIcon={<AddIcon />} variant="outlined">New Table</Button>} title="Table Explorer">
            <TextField fullWidth placeholder="Search tables, columns..." size="small" sx={{ mb: 2 }} />
            <List dense>
              {['employees', 'departments', 'salaries', 'projects', 'attendance', 'leave_requests', 'roles', 'users'].map((table, index) => (
                <ListItemButton key={table} selected={index === 0} sx={{ borderRadius: 1 }}>
                  <ListItemIcon><TableChartIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary={table} secondary={index === 0 ? 'Employee information and details' : 'Schema object'} />
                </ListItemButton>
              ))}
            </List>
          </Panel>
        </Grid>
        <Grid item md={6.6} xs={12}>
          <Panel title="Schema Viewer">
            <Grid container spacing={2}>
              {[
                ['departments', '#16a34a', ['department_id (PK)', 'department_name', 'manager_id (FK)']],
                ['employees', '#2563eb', ['employee_id (PK)', 'department_id (FK)', 'name', 'email', 'salary']],
                ['salaries', '#7c3aed', ['salary_id (PK)', 'employee_id (FK)', 'amount', 'effective_date']],
                ['projects', '#f59e0b', ['project_id (PK)', 'department_id (FK)', 'project_name', 'start_date']],
                ['attendance', '#0891b2', ['attendance_id (PK)', 'employee_id (FK)', 'date', 'status']]
              ].map(([name, color, fields]) => (
                <Grid item key={name as string} md={4} xs={12}>
                  <Stack sx={{ border: `1px solid ${color}`, borderRadius: 1, overflow: 'hidden' }}>
                    <Typography sx={{ bgcolor: `${color}22`, color, p: 1, fontWeight: 800 }} textAlign="center">{name}</Typography>
                    {(fields as string[]).map((field) => <Typography key={field} sx={{ px: 1.5, py: 0.75 }} variant="body2">{field}</Typography>)}
                  </Stack>
                </Grid>
              ))}
            </Grid>
          </Panel>
          <Panel title="Sample Data Grid">
            <DataTable columns={['employee_id', 'name', 'email', 'job_title', 'department_id', 'salary', 'is_active']} rows={[
              ['101', 'John Doe', 'john.doe@company.com', 'Software Engineer', '1', '75000.00', <StatusBadge label="1" />],
              ['102', 'Jane Smith', 'jane.smith@company.com', 'Senior Developer', '1', '85000.00', <StatusBadge label="1" />],
              ['103', 'Mike Johnson', 'mike.johnson@company.com', 'Data Analyst', '2', '65000.00', <StatusBadge label="1" />]
            ]} />
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Column Details">
            <DataTable columns={['Column', 'Type', 'Key']} rows={[
              ['employee_id', 'INT', <StatusBadge label="PRI" tone="blue" />],
              ['department_id', 'INT', <StatusBadge label="MUL" tone="purple" />],
              ['name', 'VARCHAR(100)', ''],
              ['email', 'VARCHAR(150)', <StatusBadge label="UNI" tone="orange" />],
              ['salary', 'DECIMAL(12,2)', '']
            ]} />
          </Panel>
          <Panel title="ER Diagram Placeholder">
            <Typography color="text.secondary" variant="body2">Relationship canvas boundary prepared for an interactive ER renderer.</Typography>
            <Stack spacing={1.5} sx={{ mt: 2 }}>
              <StatusBadge label="employees → departments" tone="blue" />
              <StatusBadge label="salaries → employees" tone="purple" />
              <StatusBadge label="projects → departments" tone="orange" />
            </Stack>
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
