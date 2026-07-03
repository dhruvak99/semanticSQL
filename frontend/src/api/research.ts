import { apiGet } from './client';
import { normalizeHistoryRecord, type QueryHistoryRecord, type QueryVolumePoint } from './history';

export type ResearchAnalyticsResponse = {
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
  volume_trend: QueryVolumePoint[];
  recent_queries: QueryHistoryRecord[];
};

export async function getResearchAnalytics() {
  const response = await apiGet<ResearchAnalyticsResponse>('/research/analytics');
  return {
    ...response,
    recent_queries: response.recent_queries.map(normalizeHistoryRecord)
  };
}
