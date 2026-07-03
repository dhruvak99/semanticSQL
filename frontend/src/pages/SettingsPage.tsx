import { useEffect, useState } from 'react';
import DnsOutlinedIcon from '@mui/icons-material/DnsOutlined';
import MemoryOutlinedIcon from '@mui/icons-material/MemoryOutlined';
import PsychologyOutlinedIcon from '@mui/icons-material/PsychologyOutlined';
import TuneOutlinedIcon from '@mui/icons-material/TuneOutlined';
import {
  Alert,
  Button,
  CircularProgress,
  Grid,
  Snackbar,
  Stack,
  TextField,
  Typography
} from '@mui/material';
import {
  getRuntimeSettings,
  type RuntimeSettings,
  updateCacheThreshold
} from '../api/settings';
import { DataTable, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

export function SettingsPage() {
  const [runtimeSettings, setRuntimeSettings] = useState<RuntimeSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingThreshold, setIsSavingThreshold] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [thresholdInput, setThresholdInput] = useState('');
  const [notification, setNotification] = useState<{ message: string; severity: 'success' | 'error' } | null>(null);

  async function loadSettings(signal?: AbortSignal) {
    try {
      setIsLoading(true);
      setError(null);
      const settings = await getRuntimeSettings(signal);
      setRuntimeSettings(settings);
      setThresholdInput(settings.similarity_threshold.toFixed(2));
    } catch (caughtError) {
      if (!signal?.aborted) {
        setError(caughtError instanceof Error ? caughtError.message : 'Unable to load runtime configuration.');
      }
    } finally {
      if (!signal?.aborted) {
        setIsLoading(false);
      }
    }
  }

  useEffect(() => {
    const abortController = new AbortController();
    void loadSettings(abortController.signal);
    return () => abortController.abort();
  }, []);

  async function handleSaveThreshold() {
    const threshold = Number(thresholdInput);
    if (!Number.isFinite(threshold) || threshold < 0 || threshold > 1) {
      setNotification({ message: 'Similarity threshold must be between 0.00 and 1.00.', severity: 'error' });
      return;
    }

    setIsSavingThreshold(true);
    try {
      const response = await updateCacheThreshold(threshold);
      setNotification({ message: response.message, severity: 'success' });
      await loadSettings();
    } catch (caughtError) {
      setNotification({
        message: caughtError instanceof Error ? caughtError.message : 'Unable to update similarity threshold.',
        severity: 'error'
      });
    } finally {
      setIsSavingThreshold(false);
    }
  }

  return (
    <>
      <PageHeader
        title="SemanticSQL Configuration"
        description="Inspect the runtime configuration and service availability currently used by SemanticSQL."
      />

      {error ? (
        <Alert
          action={<Button color="inherit" onClick={() => void loadSettings()} size="small">Retry</Button>}
          severity="error"
          sx={{ mb: 2 }}
        >
          {error}
        </Alert>
      ) : null}

      {isLoading ? (
        <Stack spacing={2} sx={{ alignItems: 'center', py: 6 }}>
          <CircularProgress size={28} />
          <Typography color="text.secondary" variant="body2">Loading runtime configuration...</Typography>
        </Stack>
      ) : runtimeSettings ? (
        <Grid container spacing={2.5}>
          {[
            { label: 'Active LLM Model', value: runtimeSettings.active_llm_model, icon: PsychologyOutlinedIcon, helper: 'Runtime SQL generation model', tone: 'green' },
            { label: 'Embedding Model', value: runtimeSettings.embedding_model, icon: MemoryOutlinedIcon, helper: 'Semantic cache embeddings', tone: 'purple' },
            { label: 'Cache Backend', value: runtimeSettings.cache_backend, icon: DnsOutlinedIcon, helper: runtimeSettings.redis_available ? 'Redis connected' : 'Redis unavailable', tone: runtimeSettings.redis_available ? 'blue' : 'orange' },
            { label: 'Similarity Threshold', value: runtimeSettings.similarity_threshold.toFixed(2), icon: TuneOutlinedIcon, helper: 'Current cache match threshold', tone: 'orange' }
          ].map((stat) => (
            <Grid item key={stat.label} md={3} sm={6} xs={12}>
              <StatCard {...stat} tone={stat.tone as never} />
            </Grid>
          ))}

          <Grid item md={6} xs={12}>
            <Panel title="Infrastructure Configuration">
              <DataTable
                columns={['Setting', 'Runtime Value']}
                rows={[
                  ['Redis URL', <CodeValue key="redis-url" value={runtimeSettings.redis_url} />],
                  ['Ollama URL', <CodeValue key="ollama-url" value={runtimeSettings.ollama_url} />],
                  ['Database Engine', runtimeSettings.database_engine],
                  ['Database URL', <CodeValue key="database-url" value={runtimeSettings.database_url} />]
                ]}
              />
            </Panel>
          </Grid>

          <Grid item md={6} xs={12}>
            <Panel title="Environment Information">
              <DataTable
                columns={['Setting', 'Runtime Value']}
                rows={[
                  ['SemanticSQL Version', runtimeSettings.semantic_sql_version],
                  ['Python Version', runtimeSettings.python_version],
                  ['Operating System', runtimeSettings.operating_system],
                  ['Redis Status', <ServiceStatus key="redis-status" available={runtimeSettings.redis_available} />],
                  ['Ollama Status', <ServiceStatus key="ollama-status" available={runtimeSettings.ollama_available} />]
                ]}
              />
            </Panel>
          </Grid>

          <Grid item xs={12}>
            <Panel
              title="Cache Configuration"
              subtitle="Changes apply immediately to this backend session and reset on restart."
            >
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ alignItems: { sm: 'flex-end' }, maxWidth: 440 }}>
                <TextField
                  fullWidth
                  inputProps={{ max: 1, min: 0, step: 0.01 }}
                  label="Similarity Threshold"
                  onChange={(event) => setThresholdInput(event.target.value)}
                  size="small"
                  type="number"
                  value={thresholdInput}
                />
                <Button
                  disabled={isSavingThreshold || thresholdInput === ''}
                  onClick={() => void handleSaveThreshold()}
                  sx={{ whiteSpace: 'nowrap' }}
                  variant="contained"
                >
                  {isSavingThreshold ? <CircularProgress color="inherit" size={18} /> : 'Save Threshold'}
                </Button>
              </Stack>
            </Panel>
          </Grid>
        </Grid>
      ) : (
        <Alert severity="info">No runtime configuration is available.</Alert>
      )}

      <Snackbar
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        autoHideDuration={4000}
        onClose={() => setNotification(null)}
        open={notification !== null}
      >
        {notification ? (
          <Alert onClose={() => setNotification(null)} severity={notification.severity} variant="filled">
            {notification.message}
          </Alert>
        ) : undefined}
      </Snackbar>
    </>
  );
}

function ServiceStatus({ available }: { available: boolean }) {
  return <StatusBadge label={available ? 'Connected' : 'Unavailable'} tone={available ? 'green' : 'red'} />;
}

function CodeValue({ value }: { value: string }) {
  return (
    <Typography
      component="span"
      fontFamily="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
      sx={{ overflowWrap: 'anywhere' }}
      variant="body2"
    >
      {value}
    </Typography>
  );
}
