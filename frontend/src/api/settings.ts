import { apiGet, apiPut } from './client';

export type RuntimeSettings = {
  active_llm_model: string;
  embedding_model: string;
  cache_backend: string;
  redis_url: string;
  similarity_threshold: number;
  ollama_url: string;
  database_engine: string;
  database_url: string;
  python_version: string;
  semantic_sql_version: string;
  operating_system: string;
  ollama_available: boolean;
  redis_available: boolean;
};

export function getRuntimeSettings(signal?: AbortSignal) {
  return apiGet<RuntimeSettings>('/settings/', { signal });
}

export type CacheThresholdUpdateResponse = {
  similarity_threshold: number;
  message: string;
};

export function updateCacheThreshold(similarityThreshold: number) {
  return apiPut<{ similarity_threshold: number }, CacheThresholdUpdateResponse>(
    '/settings/cache-threshold',
    { similarity_threshold: similarityThreshold }
  );
}
