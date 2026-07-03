import { env } from '../config/env';

export type OllamaModel = {
  name: string;
  size: string;
  modified: string;
  active: boolean;
};

export type ModelManagementResponse = {
  active_model: string;
  embedding_model: string;
  semantic_threshold: number;
  installed_models_count: number;
  models: OllamaModel[];
};

export type ActiveModelResponse = {
  message: string;
  active_model: string;
};

export async function getModelManagementState(signal?: AbortSignal) {
  return modelManagementRequest<ModelManagementResponse>('/model-management/', {
    method: 'GET',
    signal
  });
}

export async function setActiveModel(model: string) {
  return modelManagementRequest<ActiveModelResponse>('/model-management/active-model', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ model })
  });
}

async function modelManagementRequest<TResponse>(path: string, init: RequestInit): Promise<TResponse> {
  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...init.headers
    }
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(errorBody?.detail ?? 'Unable to retrieve installed models.');
  }

  return response.json() as Promise<TResponse>;
}
