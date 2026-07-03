import { apiGet } from './client';

export type SchemaColumn = {
  name: string;
  type: string;
  primary_key: boolean;
};

export type SchemaTable = {
  name: string;
  column_count: number;
  columns: SchemaColumn[];
};

export type DatabaseSchemaResponse = {
  table_count: number;
  column_count: number;
  tables: SchemaTable[];
};

export function getDatabaseSchema(signal?: AbortSignal) {
  return apiGet<DatabaseSchemaResponse>('/schema/', { signal });
}
