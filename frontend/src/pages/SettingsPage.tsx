import BackupIcon from '@mui/icons-material/Backup';
import CloudDoneIcon from '@mui/icons-material/CloudDone';
import KeyIcon from '@mui/icons-material/Key';
import PeopleIcon from '@mui/icons-material/People';
import SecurityIcon from '@mui/icons-material/Security';
import StorageIcon from '@mui/icons-material/Storage';
import { Button, Grid, MenuItem, Stack, Switch, TextField, Typography } from '@mui/material';
import { DataTable, MetricProgress, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function SettingsPage() {
  return (
    <>
      <PageHeader title="Settings & Administration" description="Manage user settings, database connections, cache behavior, security controls, and system preferences." />
      <Stack direction="row" spacing={1.5} sx={{ justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="outlined">System Status</Button>
        <Button>Save Changes</Button>
      </Stack>
      <Grid container spacing={2.5}>
        {[
          { label: 'System Status', value: 'Healthy', icon: SecurityIcon, helper: 'All systems operational', tone: 'green' },
          { label: 'Users', value: '23', icon: PeopleIcon, helper: 'Active users', tone: 'purple' },
          { label: 'Databases', value: '3', icon: StorageIcon, helper: 'Configured', tone: 'blue' },
          { label: 'API Keys', value: '7', icon: KeyIcon, helper: 'Active keys', tone: 'orange' },
          { label: 'Backup Status', value: 'Success', icon: BackupIcon, helper: 'Last backup: 02:30 AM', tone: 'green' },
          { label: 'License', value: 'Enterprise', icon: CloudDoneIcon, helper: 'Valid until Dec 31, 2024', tone: 'purple' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} />
          </Grid>
        ))}
        <Grid item md={4} xs={12}>
          <Panel title="User Settings">
            <DataTable columns={['User', 'Role', 'Status', 'Last Login']} rows={[
              ['admin@semanticsql.com', 'Administrator', <StatusBadge label="Active" />, 'May 21, 11:23 AM'],
              ['analyst@semanticsql.com', 'Analyst', <StatusBadge label="Active" />, 'May 21, 10:45 AM'],
              ['developer@semanticsql.com', 'Developer', <StatusBadge label="Active" />, 'May 21, 09:12 AM'],
              ['readonly@semanticsql.com', 'Viewer', <StatusBadge label="Inactive" tone="gray" />, 'May 18, 11:02 AM']
            ]} />
            <Button sx={{ mt: 2 }} variant="outlined">Add New User</Button>
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Database Settings">
            <DataTable columns={['Connection', 'Type', 'Host', 'Status']} rows={[
              ['MySQL - Main DB', 'MySQL 8.0', '192.168.1.101:3306', <StatusBadge label="Connected" />],
              ['Analytics DB', 'MySQL 8.0', '192.168.1.102:3306', <StatusBadge label="Connected" />],
              ['Reporting DB', 'MySQL 8.0', '192.168.1.103:3306', <StatusBadge label="Connected" />]
            ]} />
            <Button sx={{ mt: 2 }} variant="outlined">Add Connection</Button>
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Security Settings">
            <DataTable columns={['Key', 'Preview', 'Permissions', 'Status']} rows={[
              ['Production Key', 'sk_live_••••••••', 'Full Access', <StatusBadge label="Active" />],
              ['Development Key', 'sk_dev_••••••••', 'Full Access', <StatusBadge label="Active" />],
              ['Read Only Key', 'sk_ro_••••••••', 'Read Only', <StatusBadge label="Active" />]
            ]} />
            <Button sx={{ mt: 2 }} variant="outlined">Generate New Key</Button>
          </Panel>
        </Grid>
        <Grid item md={3.2} xs={12}>
          <Panel title="Cache Settings">
            <Stack spacing={1.5}>
              <TextField defaultValue="127.0.0.1" label="Redis Host" size="small" />
              <TextField defaultValue="6379" label="Redis Port" size="small" />
              <TextField defaultValue="3600" label="Default TTL (seconds)" size="small" />
              <MetricProgress label="Max Memory" value={64} detail="2 GB allocated" tone="blue" />
              <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}><Typography variant="body2">Enable Compression</Typography><Switch defaultChecked /></Stack>
            </Stack>
          </Panel>
        </Grid>
        <Grid item md={3.2} xs={12}>
          <Panel title="Backup & Restore">
            <Stack spacing={1.5}>
              <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}><Typography variant="body2">Automatic Backup</Typography><Switch defaultChecked /></Stack>
              <TextField defaultValue="Daily" label="Backup Frequency" select size="small"><MenuItem value="Daily">Daily</MenuItem></TextField>
              <TextField defaultValue="30" label="Retention Period" size="small" />
              <Button variant="outlined">Run Backup Now</Button>
              <Button variant="outlined">Restore from Backup</Button>
            </Stack>
          </Panel>
        </Grid>
        <Grid item md={2.8} xs={12}>
          <Panel title="Notification Settings">
            {['System Alerts', 'Error Notifications', 'Query Failures', 'Performance Alerts', 'Daily Reports'].map((label, index) => (
              <Stack direction="row" key={label} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="body2">{label}</Typography>
                <Switch checked={index < 4} size="small" />
              </Stack>
            ))}
          </Panel>
        </Grid>
        <Grid item md={2.8} xs={12}>
          <Panel title="System Actions">
            <Stack spacing={1}>
              {['Clear All Caches', 'Rebuild Embeddings', 'Database Health Check', 'Optimize Database', 'Restart Services'].map((action, index) => (
                <Button color={index === 4 ? 'error' : 'primary'} key={action} variant="outlined">{action}</Button>
              ))}
            </Stack>
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
