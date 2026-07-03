import { env } from '../config/env';
import { normalizeGenerationMode } from '../utils/generationMode';

export type DatabaseTableSummary = {
  name: string;
  row_count: number;
};

export type DatabaseTablesResponse = {
  tables: DatabaseTableSummary[];
};

export type DatabaseTableDataResponse = {
  table_name: string;
  columns: string[];
  rows: Array<Array<string | number | boolean | null>>;
  total_rows: number;
  page: number;
  page_size: number;
};

export async function getDatabaseTables(signal?: AbortSignal): Promise<DatabaseTablesResponse> {
  return databaseExplorerGet<DatabaseTablesResponse>('/database/tables', signal);
}

export async function getDatabaseTableData(
  tableName: string,
  page: number,
  pageSize: number,
  signal?: AbortSignal
): Promise<DatabaseTableDataResponse> {
  const searchParams = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize)
  });

  const response = await databaseExplorerGet<DatabaseTableDataResponse>(
    `/database/table/${encodeURIComponent(tableName)}?${searchParams.toString()}`,
    signal
  );

  if (response.table_name !== 'query_history') {
    return response;
  }

  const generationModeIndex = response.columns.indexOf('generation_mode');
  if (generationModeIndex < 0) {
    return response;
  }

  return {
    ...response,
    rows: response.rows.map((row) => row.map((value, index) => (
      index === generationModeIndex && typeof value === 'string'
        ? normalizeGenerationMode(value)
        : value
    )))
  };
}

async function databaseExplorerGet<TResponse>(path: string, signal?: AbortSignal): Promise<TResponse> {
  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json'
    },
    signal
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(errorBody?.detail ?? `API request failed with status ${response.status}`);
  }

  return response.json() as Promise<TResponse>;
}
