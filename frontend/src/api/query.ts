import { apiPost } from './client';
import { normalizeGenerationMode, type GenerationMode } from '../utils/generationMode';

export type QueryProcessRequest = {
  query: string;
};

export type QueryResultRow = Record<string, string | number | boolean | null>;

export type QueryProcessResponse = {
  generation_mode: GenerationMode;
  generated_sql: string;
  corrected_sql: string | null;
  executed_sql: string | null;
  validation: {
    valid: boolean;
    errors: string[];
  };
  cache_hit: boolean;
  similarity_score: number;
  validation_status: 'valid' | 'invalid';
  validation_errors: string[];
  execution_time: number;
  rows_returned: number;
  results: QueryResultRow[];
};

export async function processQuery(query: string) {
  const response = await apiPost<QueryProcessRequest, QueryProcessResponse>('/query/process', { query });
  return {
    ...response,
    generation_mode: normalizeGenerationMode(response.generation_mode)
  };
}
