import AddIcon from '@mui/icons-material/Add';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import DataObjectIcon from '@mui/icons-material/DataObject';
import MemoryIcon from '@mui/icons-material/Memory';
import PaidIcon from '@mui/icons-material/Paid';
import SpeedIcon from '@mui/icons-material/Speed';
import TokenIcon from '@mui/icons-material/Token';
import { Button, Grid, MenuItem, Slider, Stack, TextField, Typography } from '@mui/material';
import { CodeBlock, DataTable, DonutChart, LineChart, MetricProgress, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function ModelManagementPage() {
  return (
    <>
      <PageHeader title="Model Management" description="Manage active models, prompt templates, thresholds, correction policies, and runtime statistics." />
      <Stack direction="row" spacing={1.5} sx={{ justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="outlined">Compare Models</Button>
        <Button startIcon={<AddIcon />}>Add New Model</Button>
      </Stack>
      <Grid container spacing={2.5}>
        {[
          { label: 'Active Model', value: 'gpt-4o', icon: MemoryIcon, helper: 'SQL generation default', tone: 'blue' },
          { label: 'Inference Requests', value: '125,240', icon: DataObjectIcon, trend: '18.6% vs last 7 days', tone: 'green' },
          { label: 'Avg Tokens / Request', value: '1,842', icon: TokenIcon, trend: '7.3% vs last 7 days', tone: 'purple' },
          { label: 'Model Success Rate', value: '96.8%', icon: AutoFixHighIcon, trend: '2.1% vs last 7 days', tone: 'green' },
          { label: 'Total Cost (7D)', value: '$48.72', icon: PaidIcon, trend: '12.4% vs last 7 days', tone: 'purple' },
          { label: 'Avg Latency', value: '0.842 sec', icon: SpeedIcon, trend: '8.6% faster', tone: 'cyan' }
        ].map((stat) => (
          <Grid item key={stat.label} md={2} sm={6} xs={12}>
            <StatCard {...stat} tone={stat.tone as never} />
          </Grid>
        ))}
        <Grid item md={4} xs={12}>
          <Panel title="Active Model Inventory">
            <DataTable columns={['Model', 'Type', 'Provider', 'Status', 'Version']} rows={[
              ['gpt-4o', 'LLM', 'OpenAI', <StatusBadge label="Active" />, '2024-05-13'],
              ['gpt-4o-mini', 'LLM', 'OpenAI', <StatusBadge label="Active" />, '2024-05-10'],
              ['text-embedding-3-large', 'Embedding', 'OpenAI', <StatusBadge label="Active" />, '2024-05-12'],
              ['mistral-large-2', 'LLM', 'Mistral AI', <StatusBadge label="Inactive" tone="gray" />, '2024-04-28']
            ]} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Model Statistics">
            <LineChart color="#7c3aed" data={[94, 96, 95, 92, 97, 93, 96]} secondaryData={[76, 82, 79, 83, 78, 81, 88]} height={210} />
          </Panel>
        </Grid>
        <Grid item md={4} xs={12}>
          <Panel title="Similarity Threshold Controls">
            <Stack spacing={2}>
              <TextField defaultValue="gpt-4o" fullWidth label="Default LLM" select size="small"><MenuItem value="gpt-4o">gpt-4o</MenuItem></TextField>
              <TextField defaultValue="text-embedding-3-large" fullWidth label="Embedding Model" select size="small"><MenuItem value="text-embedding-3-large">text-embedding-3-large</MenuItem></TextField>
              <Typography variant="body2">Semantic Cache Threshold: <strong>0.85</strong></Typography>
              <Slider defaultValue={85} />
              <Typography variant="body2">Fuzzy Match Threshold: <strong>0.70</strong></Typography>
              <Slider defaultValue={70} />
              <MetricProgress label="Top-K Result Budget" value={30} detail="15 of 50 candidates" tone="purple" />
            </Stack>
          </Panel>
        </Grid>
        <Grid item md={4.5} xs={12}>
          <Panel title="Prompt Templates">
            <DataTable columns={['Template', 'Type', 'Uses (7D)', 'Status']} rows={[
              ['sql_generation_v2', 'SQL Generation', '48,210', <StatusBadge label="Active" />],
              ['sql_correction_v2', 'SQL Correction', '22,134', <StatusBadge label="Active" />],
              ['schema_extraction_v1', 'Schema Understanding', '8,921', <StatusBadge label="Active" />],
              ['query_rewrite_v1', 'Query Rewrite', '6,214', <StatusBadge label="Inactive" tone="gray" />]
            ]} />
          </Panel>
        </Grid>
        <Grid item md={4.5} xs={12}>
          <Panel title="Prompt Testing Playground">
            <TextField fullWidth multiline minRows={3} size="small" value="Show me total revenue by month for the last year" />
            <CodeBlock code={`SELECT DATE_FORMAT(order_date, '%Y-%m') AS month,\n       SUM(total_amount) AS total_revenue\nFROM orders\nWHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)\nGROUP BY month\nORDER BY month;`} />
            <Stack direction="row" spacing={2} sx={{ mt: 1 }}><StatusBadge label="0.742s" tone="blue" /><StatusBadge label="512 tokens" tone="purple" /><StatusBadge label="Success" /></Stack>
          </Panel>
        </Grid>
        <Grid item md={3} xs={12}>
          <Panel title="Model Cost & Usage">
            <DonutChart centerLabel="$48.72" segments={[{ label: 'gpt-4o', value: 49.6, color: '#7c3aed' }, { label: 'gpt-4o-mini', value: 25.3, color: '#2563eb' }, { label: 'mistral', value: 16.1, color: '#16a34a' }, { label: 'others', value: 9, color: '#f59e0b' }]} />
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}
