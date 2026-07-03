import { useEffect, useMemo, useState } from 'react';
import KeyIcon from '@mui/icons-material/Key';
import SearchIcon from '@mui/icons-material/Search';
import TableChartIcon from '@mui/icons-material/TableChart';
import ViewColumnIcon from '@mui/icons-material/ViewColumn';
import { Alert, Button, CircularProgress, Grid, InputAdornment, Stack, TextField, Typography } from '@mui/material';
import { getDatabaseSchema, type DatabaseSchemaResponse, type SchemaTable } from '../api/schema';
import { DataTable, Panel, StatCard, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

const emptySchema: DatabaseSchemaResponse = {
  table_count: 0,
  column_count: 0,
  tables: []
};

export function SchemaManagerPage() {
  const [schema, setSchema] = useState<DatabaseSchemaResponse>(emptySchema);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTableName, setSelectedTableName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSchema() {
      try {
        setIsLoading(true);
        setError(null);
        const response = await getDatabaseSchema();
        setSchema(response);
        setSelectedTableName((current) => current ?? response.tables[0]?.name ?? null);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : 'Failed to load database schema');
      } finally {
        setIsLoading(false);
      }
    }

    void loadSchema();
  }, []);

  const filteredTables = useMemo(() => {
    const normalizedSearchTerm = searchTerm.trim().toLowerCase();
    if (!normalizedSearchTerm) {
      return schema.tables;
    }

    return schema.tables.filter((table) => table.name.toLowerCase().includes(normalizedSearchTerm));
  }, [schema.tables, searchTerm]);

  const selectedTable = schema.tables.find((table) => table.name === selectedTableName) ?? filteredTables[0];

  return (
    <>
      <PageHeader title="Schema Manager" description="Browse the active SQLite tables, columns, data types, and primary keys." />
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}
      <Grid container spacing={2.5}>
        <Grid item md={3} sm={6} xs={12}>
          <StatCard icon={TableChartIcon} label="Total Tables" tone="blue" trend="Active SQLite schema" value={schema.table_count.toLocaleString()} />
        </Grid>
        <Grid item md={3} sm={6} xs={12}>
          <StatCard icon={ViewColumnIcon} label="Total Columns" tone="green" trend="Across all tables" value={schema.column_count.toLocaleString()} />
        </Grid>

        <Grid item xs={12}>
          <Panel title="Database Tables">
            <TextField
              fullWidth
              InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> }}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search tables..."
              size="small"
              sx={{ mb: 2, maxWidth: 420 }}
              value={searchTerm}
            />
            {isLoading ? <CircularProgress size={22} /> : filteredTables.length > 0 ? (
              <DataTable
                columns={['Table Name', 'Column Count']}
                rows={filteredTables.map((table) => [
                  <Button key={table.name} onClick={() => setSelectedTableName(table.name)} sx={{ justifyContent: 'flex-start', px: 0 }} variant="text">
                    {table.name}
                  </Button>,
                  table.column_count
                ])}
              />
            ) : (
              <EmptyState message={schema.table_count === 0 ? 'No SQLite tables found.' : 'No tables match your search.'} />
            )}
          </Panel>
        </Grid>

        <Grid item xs={12}>
          <Panel title={selectedTable ? `Table Details: ${selectedTable.name}` : 'Table Details'}>
            {isLoading ? <CircularProgress size={22} /> : selectedTable ? (
              <DataTable
                columns={['Column Name', 'Data Type', 'Primary Key']}
                rows={columnRows(selectedTable)}
              />
            ) : (
              <EmptyState message="Select a table to inspect its columns." />
            )}
          </Panel>
        </Grid>
      </Grid>
    </>
  );
}

function columnRows(table: SchemaTable) {
  return table.columns.map((column) => [
    column.name,
    column.type,
    column.primary_key
      ? <StatusBadge key={column.name} label="Yes" tone="blue" />
      : <StatusBadge key={column.name} label="No" tone="gray" />
  ]);
}

function EmptyState({ message }: { message: string }) {
  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
      <KeyIcon color="disabled" fontSize="small" />
      <Typography color="text.secondary" variant="body2">
        {message}
      </Typography>
    </Stack>
  );
}
