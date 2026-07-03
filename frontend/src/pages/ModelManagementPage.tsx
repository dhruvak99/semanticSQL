import { useEffect, useState } from 'react';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HubIcon from '@mui/icons-material/Hub';
import MemoryIcon from '@mui/icons-material/Memory';
import TuneIcon from '@mui/icons-material/Tune';
import {
  Alert,
  Button,
  CircularProgress,
  Grid,
  Snackbar,
  Stack,
  Typography
} from '@mui/material';
import {
  getModelManagementState,
  setActiveModel,
  type ModelManagementResponse
} from '../api/modelManagement';
import { DataTable, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

type Notification = {
  message: string;
  severity: 'success' | 'error';
};

export function ModelManagementPage() {
  const [modelState, setModelState] = useState<ModelManagementResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [switchingModel, setSwitchingModel] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<Notification | null>(null);

  async function loadModels(signal?: AbortSignal) {
    try {
      setIsLoading(true);
      setError(null);
      setModelState(await getModelManagementState(signal));
    } catch (caughtError) {
      if (!signal?.aborted) {
        setError(caughtError instanceof Error ? caughtError.message : 'Unable to retrieve installed models.');
      }
    } finally {
      if (!signal?.aborted) {
        setIsLoading(false);
      }
    }
  }

  useEffect(() => {
    const abortController = new AbortController();
    void loadModels(abortController.signal);
    return () => abortController.abort();
  }, []);

  async function handleSetActive(model: string) {
    if (!modelState || switchingModel) {
      return;
    }

    setSwitchingModel(model);
    try {
      const response = await setActiveModel(model);
      setModelState({
        ...modelState,
        active_model: response.active_model,
        models: modelState.models.map((installedModel) => ({
          ...installedModel,
          active: installedModel.name === response.active_model
        }))
      });
      setNotification({ message: response.message, severity: 'success' });
    } catch (caughtError) {
      setNotification({
        message: caughtError instanceof Error ? caughtError.message : 'Unable to update the active model.',
        severity: 'error'
      });
    } finally {
      setSwitchingModel(null);
    }
  }

  const modelRows = modelState?.models.map((model) => [
    <Typography key={`${model.name}-name`} fontFamily="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" variant="body2">
      {model.name}
    </Typography>,
    model.size,
    model.modified,
    <StatusBadge key={`${model.name}-status`} label={model.active ? 'Active' : 'Available'} tone={model.active ? 'green' : 'gray'} />,
    model.active ? (
      <Typography key={`${model.name}-active`} color="text.secondary" variant="body2">Current model</Typography>
    ) : (
      <Button
        key={`${model.name}-action`}
        disabled={switchingModel !== null}
        onClick={() => void handleSetActive(model.name)}
        size="small"
        variant="outlined"
      >
        {switchingModel === model.name ? <CircularProgress size={16} /> : 'Set Active'}
      </Button>
    )
  ]) ?? [];

  return (
    <>
      <PageHeader title="Model Management" description="Inspect locally installed Ollama models and select the runtime SQL generation model." />
      {error ? (
        <Alert
          action={<Button color="inherit" onClick={() => void loadModels()} size="small">Retry</Button>}
          severity="error"
          sx={{ mb: 2 }}
        >
          {error}
        </Alert>
      ) : null}

      {isLoading ? (
        <Stack spacing={2} sx={{ alignItems: 'center', py: 6 }}>
          <CircularProgress size={28} />
          <Typography color="text.secondary" variant="body2">Loading Ollama models...</Typography>
        </Stack>
      ) : modelState ? (
        <Grid container spacing={2.5}>
          {[
            { label: 'Active Model', value: modelState.active_model, icon: CheckCircleOutlineIcon, helper: 'Runtime SQL generation model', tone: 'green' },
            { label: 'Installed Models', value: modelState.installed_models_count.toLocaleString(), icon: HubIcon, helper: 'Available in local Ollama', tone: 'blue' },
            { label: 'Embedding Model', value: modelState.embedding_model, icon: MemoryIcon, helper: 'Semantic cache embeddings', tone: 'purple' },
            { label: 'Semantic Threshold', value: modelState.semantic_threshold.toFixed(2), icon: TuneIcon, helper: 'Cache similarity threshold', tone: 'orange' }
          ].map((stat) => (
            <Grid item key={stat.label} md={3} sm={6} xs={12}>
              <StatCard {...stat} tone={stat.tone as never} />
            </Grid>
          ))}

          <Grid item xs={12}>
            <Panel title="Installed Ollama Models">
              {modelState.models.length === 0 ? (
                <Typography color="text.secondary" variant="body2">
                  No Ollama models were found.
                  Install models using 'ollama pull'.
                </Typography>
              ) : (
                <DataTable
                  columns={['Model Name', 'Size', 'Last Modified', 'Status', 'Action']}
                  rows={modelRows}
                />
              )}
            </Panel>
          </Grid>
        </Grid>
      ) : null}

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
