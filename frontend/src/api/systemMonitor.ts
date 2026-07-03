import { apiGet } from './client';
import { normalizeHistoryRecord, type QueryHistoryRecord, type QueryVolumePoint } from './history';

export type RecentFailure = {
  natural_language_query: string;
  generated_sql: string;
  failure_type: string;
  created_at: string;
};

export type SystemMonitorResponse = {
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
  average_execution_time: number;
  schema_mismatches: number;
  llm_queries: number;
  rule_queries: number;
  recent_failures: RecentFailure[];
  recent_activity: QueryHistoryRecord[];
  query_volume_trend: QueryVolumePoint[];
};

export async function getSystemMonitorMetrics() {
  const response = await apiGet<SystemMonitorResponse>('/system-monitor/');
  return {
    ...response,
    recent_activity: response.recent_activity.map(normalizeHistoryRecord)
  };
}
