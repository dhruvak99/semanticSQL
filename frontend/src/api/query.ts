import { apiPost } from './client';

export type QueryProcessRequest = {
  query: string;
};

export type QueryResultRow = Record<string, string | number | boolean | null>;

export type QueryProcessResponse = {
  generated_sql: string;
  cache_hit: boolean;
  validation_status: 'valid' | 'invalid';
  execution_time: number;
  rows_returned: number;
  results: QueryResultRow[];
};

export function processQuery(query: string) {
  return apiPost<QueryProcessRequest, QueryProcessResponse>('/query/process', { query });
}
