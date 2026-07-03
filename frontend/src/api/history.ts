import { apiGet } from './client';
import { normalizeGenerationMode, type GenerationMode } from '../utils/generationMode';

export type QueryHistoryRecord = {
  id: number;
  natural_language_query: string;
  generated_sql: string;
  generation_mode: GenerationMode;
  cache_status: string;
  validation_status: string;
  execution_time: number;
  rows_returned: number;
  created_at: string;
};

export type QueryHistoryResponse = {
  items: QueryHistoryRecord[];
};

export type QueryVolumePoint = {
  date: string;
  count: number;
};

export type QueryAnalyticsResponse = {
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
  average_execution_time: number;
  rule_generation_count: number;
  llm_generation_count: number;
  schema_mismatch_count: number;
  volume_trend: QueryVolumePoint[];
  recent_queries: QueryHistoryRecord[];
};

export type ValidationFailureRecord = {
  natural_language_query: string;
  generated_sql: string;
  validation_status: string;
  failure_type: string;
  created_at: string;
};

export type ValidationAnalyticsResponse = {
  total_validated_queries: number;
  valid_queries: number;
  invalid_queries: number;
  validation_success_rate: number;
  schema_mismatch_count: number;
  cache_hit_count: number;
  cache_miss_count: number;
  validation_logs: QueryHistoryRecord[];
  recent_failures: ValidationFailureRecord[];
};

export async function getQueryHistory(limit = 100) {
  return normalizeHistoryResponse(await apiGet<QueryHistoryResponse>(`/history/?limit=${limit}`));
}

export async function getQueryAnalytics() {
  const response = await apiGet<QueryAnalyticsResponse>('/history/analytics');
  return {
    ...response,
    recent_queries: response.recent_queries.map(normalizeHistoryRecord)
  };
}

export async function getValidationAnalytics() {
  const response = await apiGet<ValidationAnalyticsResponse>('/history/validation-analytics');
  return {
    ...response,
    validation_logs: response.validation_logs.map(normalizeHistoryRecord)
  };
}

export function normalizeHistoryRecord(record: QueryHistoryRecord): QueryHistoryRecord {
  return {
    ...record,
    generation_mode: normalizeGenerationMode(record.generation_mode)
  };
}

function normalizeHistoryResponse(response: QueryHistoryResponse): QueryHistoryResponse {
  return {
    items: response.items.map(normalizeHistoryRecord)
  };
}
