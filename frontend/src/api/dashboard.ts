import { apiGet } from './client';
import { normalizeHistoryRecord, type QueryHistoryRecord, type QueryVolumePoint } from './history';

export type DashboardResponse = {
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
  average_execution_time: number;
  llm_queries: number;
  rule_queries: number;
  schema_mismatches: number;
  recent_queries: QueryHistoryRecord[];
  query_volume_trend: QueryVolumePoint[];
};

export async function getDashboardMetrics() {
  const response = await apiGet<DashboardResponse>('/dashboard/');
  return {
    ...response,
    recent_queries: response.recent_queries.map(normalizeHistoryRecord)
  };
}
