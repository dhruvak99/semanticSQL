import { apiGet } from './client';

export type TopCachedQuery = {
  query: string;
  generated_sql: string;
  hit_count: number;
  last_similarity_score: number;
  timestamp: string;
};

export type SemanticCacheMetrics = {
  backend: 'redis' | 'memory';
  cache_hits: number;
  cache_misses: number;
  hit_rate: number;
  average_similarity_score: number;
  cache_entry_count: number;
  top_cached_queries: TopCachedQuery[];
};

export function getSemanticCacheMetrics() {
  return apiGet<SemanticCacheMetrics>('/cache/');
}
