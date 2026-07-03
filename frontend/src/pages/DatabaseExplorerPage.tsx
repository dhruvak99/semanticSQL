import { useEffect, useMemo, useState } from 'react';
import KeyIcon from '@mui/icons-material/Key';
import SearchIcon from '@mui/icons-material/Search';
import TableChartIcon from '@mui/icons-material/TableChart';
import {
  Alert,
  Box,
  Button,
  Card,
  CircularProgress,
  Divider,
  FormControl,
  InputAdornment,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography
} from '@mui/material';
import {
  getDatabaseTableData,
  getDatabaseTables,
  type DatabaseTableDataResponse,
  type DatabaseTableSummary
} from '../api/databaseExplorer';
import { getDatabaseSchema, type DatabaseSchemaResponse } from '../api/schema';
import { DataTable, StatusBadge } from '../components/common/EnterpriseDashboard';
import { PageHeader } from '../components/common/PageHeader';

const pageSizeOptions = [10, 20, 50, 100];
type ExplorerTab = 'structure' | 'data';

export function DatabaseExplorerPage() {
  const [tables, setTables] = useState<DatabaseTableSummary[]>([]);
  const [schema, setSchema] = useState<DatabaseSchemaResponse | null>(null);
  const [selectedTableName, setSelectedTableName] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ExplorerTab>('structure');
  const [tableData, setTableData] = useState<DatabaseTableDataResponse | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [dataReloadKey, setDataReloadKey] = useState(0);
  const [isTablesLoading, setIsTablesLoading] = useState(true);
  const [isSchemaLoading, setIsSchemaLoading] = useState(true);
  const [isDataLoading, setIsDataLoading] = useState(false);
  const [tablesError, setTablesError] = useState<string | null>(null);
  const [schemaError, setSchemaError] = useState<string | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);

  async function loadTables(signal?: AbortSignal) {
    try {
      setIsTablesLoading(true);
      setTablesError(null);
      const response = await getDatabaseTables(signal);
      setTables(response.tables);
      setSelectedTableName((current) => (
        current && response.tables.some((table) => table.name === current)
          ? current
          : response.tables[0]?.name ?? null
      ));
    } catch (caughtError) {
      if (!signal?.aborted) {
        setTablesError(caughtError instanceof Error ? caughtError.message : 'Failed to load database tables');
      }
    } finally {
      if (!signal?.aborted) {
        setIsTablesLoading(false);
      }
    }
  }

  async function loadSchema(signal?: AbortSignal) {
    try {
      setIsSchemaLoading(true);
      setSchemaError(null);
      setSchema(await getDatabaseSchema(signal));
    } catch (caughtError) {
      if (!signal?.aborted) {
        setSchemaError(caughtError instanceof Error ? caughtError.message : 'Failed to load table structure');
      }
    } finally {
      if (!signal?.aborted) {
        setIsSchemaLoading(false);
      }
    }
  }

  useEffect(() => {
    const abortController = new AbortController();
    void loadTables(abortController.signal);
    void loadSchema(abortController.signal);
    return () => abortController.abort();
  }, []);

  useEffect(() => {
    if (!selectedTableName || activeTab !== 'data') {
      return;
    }

    const tableName = selectedTableName;
    const abortController = new AbortController();

    async function loadTableData() {
      try {
        setIsDataLoading(true);
        setDataError(null);
        setTableData(await getDatabaseTableData(tableName, page, pageSize, abortController.signal));
      } catch (caughtError) {
        if (!abortController.signal.aborted) {
          setTableData(null);
          setDataError(caughtError instanceof Error ? caughtError.message : 'Failed to load table data');
        }
      } finally {
        if (!abortController.signal.aborted) {
          setIsDataLoading(false);
        }
      }
    }

    void loadTableData();
    return () => abortController.abort();
  }, [activeTab, dataReloadKey, page, pageSize, selectedTableName]);

  const filteredTables = useMemo(() => {
    const normalizedSearchTerm = searchTerm.trim().toLowerCase();
    return normalizedSearchTerm
      ? tables.filter((table) => table.name.toLowerCase().includes(normalizedSearchTerm))
      : tables;
  }, [searchTerm, tables]);

  const selectedTable = tables.find((table) => table.name === selectedTableName) ?? null;
  const selectedSchema = schema?.tables.find((table) => table.name === selectedTableName) ?? null;
  const totalPages = Math.max(1, Math.ceil((tableData?.total_rows ?? selectedTable?.row_count ?? 0) / pageSize));

  function selectTable(tableName: string) {
    setSelectedTableName(tableName);
    setActiveTab('structure');
    setTableData(null);
    setDataError(null);
    setPage(1);
  }

  return (
    <>
      <PageHeader title="Database Explorer" description="Inspect live SQLite table structures and records in read-only mode." />
      <Card sx={{ minHeight: 640, overflow: 'hidden' }}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '280px minmax(0, 1fr)' },
            minHeight: 640
          }}
        >
          <Box sx={{ borderRight: { md: '1px solid' }, borderBottom: { xs: '1px solid', md: 0 }, borderColor: 'divider', bgcolor: '#fbfcfe' }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', px: 2, py: 1.75 }}>
              <TableChartIcon color="primary" fontSize="small" />
              <Typography fontWeight={800} variant="subtitle2">Tables</Typography>
              <Typography color="text.secondary" sx={{ ml: 'auto !important' }} variant="caption">
                {tables.length}
              </Typography>
            </Stack>
            <Divider />
            <Box sx={{ p: 1.5 }}>
              <TextField
                fullWidth
                InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> }}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search tables"
                size="small"
                value={searchTerm}
              />
            </Box>

            {isTablesLoading ? (
              <LoadingState label="Loading tables..." />
            ) : tablesError ? (
              <ErrorState message={tablesError} onRetry={() => void loadTables()} />
            ) : tables.length === 0 ? (
              <EmptyState message="No database tables available." />
            ) : filteredTables.length === 0 ? (
              <EmptyState message="No tables match your search." />
            ) : (
              <List dense disablePadding sx={{ px: 1, pb: 2 }}>
                {filteredTables.map((table) => (
                  <ListItemButton
                    key={table.name}
                    onClick={() => selectTable(table.name)}
                    selected={table.name === selectedTableName}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      py: 0.75,
                      '&.Mui-selected': {
                        bgcolor: '#eaf1ff',
                        borderLeft: '3px solid',
                        borderColor: 'primary.main'
                      }
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 34 }}>
                      <TableChartIcon color={table.name === selectedTableName ? 'primary' : 'action'} fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={table.name}
                      primaryTypographyProps={{ fontSize: 13, fontWeight: table.name === selectedTableName ? 800 : 600 }}
                      secondary={`${table.row_count.toLocaleString()} rows`}
                      secondaryTypographyProps={{ fontSize: 11 }}
                    />
                  </ListItemButton>
                ))}
              </List>
            )}
          </Box>

          <Box sx={{ minWidth: 0 }}>
            {!selectedTable ? (
              <EmptyState message={isTablesLoading ? 'Loading database tables...' : 'Select a table to inspect it.'} />
            ) : (
              <>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between', px: 2.5, py: 2 }}>
                  <Box>
                    <Typography variant="h6">{selectedTable.name}</Typography>
                    <Stack direction="row" spacing={2.5} sx={{ mt: 0.5 }}>
                      <Typography color="text.secondary" variant="body2">
                        Rows: <strong>{selectedTable.row_count.toLocaleString()}</strong>
                      </Typography>
                      <Typography color="text.secondary" variant="body2">
                        Columns: <strong>{selectedSchema?.column_count ?? '-'}</strong>
                      </Typography>
                    </Stack>
                  </Box>
                  <StatusBadge label="Read Only" tone="gray" />
                </Stack>
                <Divider />
                <Tabs
                  onChange={(_, value: ExplorerTab) => setActiveTab(value)}
                  sx={{ minHeight: 44, px: 1.5 }}
                  value={activeTab}
                >
                  <Tab label="Structure" sx={{ minHeight: 44 }} value="structure" />
                  <Tab label="Data" sx={{ minHeight: 44 }} value="data" />
                </Tabs>
                <Divider />

                <Box sx={{ p: 2.5 }}>
                  {activeTab === 'structure' ? (
                    <StructureView
                      isLoading={isSchemaLoading}
                      error={schemaError}
                      onRetry={() => void loadSchema()}
                      table={selectedSchema}
                    />
                  ) : (
                    <DataView
                      data={tableData}
                      error={dataError}
                      isLoading={isDataLoading}
                      onNext={() => setPage((current) => current + 1)}
                      onPageSizeChange={(value) => {
                        setPageSize(value);
                        setPage(1);
                      }}
                      onPrevious={() => setPage((current) => Math.max(1, current - 1))}
                      onRetry={() => {
                        setTableData(null);
                        setDataError(null);
                        setDataReloadKey((current) => current + 1);
                      }}
                      page={page}
                      pageSize={pageSize}
                      totalPages={totalPages}
                    />
                  )}
                </Box>
              </>
            )}
          </Box>
        </Box>
      </Card>
    </>
  );
}

function StructureView({
  error,
  isLoading,
  onRetry,
  table
}: {
  error: string | null;
  isLoading: boolean;
  onRetry: () => void;
  table: DatabaseSchemaResponse['tables'][number] | null;
}) {
  if (isLoading) {
    return <LoadingState label="Loading table structure..." />;
  }
  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }
  if (!table) {
    return <EmptyState message="No structure metadata is available for this table." />;
  }

  return (
    <DataTable
      columns={['Column Name', 'Data Type', 'Primary Key']}
      rows={table.columns.map((column) => [
        <Stack key={column.name} direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          {column.primary_key ? <KeyIcon color="primary" sx={{ fontSize: 16 }} /> : <Box sx={{ width: 16 }} />}
          <Typography fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace" variant="body2">{column.name}</Typography>
        </Stack>,
        column.type,
        <StatusBadge key={`${column.name}-pk`} label={column.primary_key ? 'Yes' : 'No'} tone={column.primary_key ? 'blue' : 'gray'} />
      ])}
    />
  );
}

function DataView({
  data,
  error,
  isLoading,
  onNext,
  onPageSizeChange,
  onPrevious,
  onRetry,
  page,
  pageSize,
  totalPages
}: {
  data: DatabaseTableDataResponse | null;
  error: string | null;
  isLoading: boolean;
  onNext: () => void;
  onPageSizeChange: (value: number) => void;
  onPrevious: () => void;
  onRetry: () => void;
  page: number;
  pageSize: number;
  totalPages: number;
}) {
  if (isLoading) {
    return <LoadingState label="Loading table data..." />;
  }
  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }
  if (!data) {
    return <LoadingState label="Loading table data..." />;
  }

  return (
    <Stack spacing={2}>
      {data.rows.length > 0 ? (
        <DataTable columns={data.columns} rows={formatRows(data.rows)} />
      ) : (
        <EmptyState message="This table contains no records." />
      )}
      <Divider />
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between' }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <Typography color="text.secondary" variant="body2">Page size</Typography>
          <FormControl size="small" sx={{ minWidth: 82 }}>
            <Select onChange={(event) => onPageSizeChange(Number(event.target.value))} value={pageSize}>
              {pageSizeOptions.map((option) => <MenuItem key={option} value={option}>{option}</MenuItem>)}
            </Select>
          </FormControl>
          <Typography color="text.secondary" variant="body2">
            {data.total_rows.toLocaleString()} rows
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <Button disabled={page <= 1} onClick={onPrevious} variant="outlined">Previous</Button>
          <Typography sx={{ minWidth: 90, textAlign: 'center' }} variant="body2">
            Page {page} of {totalPages}
          </Typography>
          <Button disabled={page >= totalPages} onClick={onNext} variant="outlined">Next</Button>
        </Stack>
      </Stack>
    </Stack>
  );
}

function formatRows(rows: DatabaseTableDataResponse['rows']) {
  return rows.map((row) => row.map(formatCellValue));
}

function formatCellValue(value: string | number | boolean | null) {
  if (value === null) {
    return <Typography color="text.secondary" variant="body2">NULL</Typography>;
  }
  return typeof value === 'boolean' ? String(value) : String(value);
}

function LoadingState({ label }: { label: string }) {
  return (
    <Stack direction="row" spacing={1.25} sx={{ alignItems: 'center', p: 2 }}>
      <CircularProgress size={18} />
      <Typography color="text.secondary" variant="body2">{label}</Typography>
    </Stack>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <Alert action={<Button color="inherit" onClick={onRetry} size="small">Retry</Button>} severity="error">
      {message}
    </Alert>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <Typography color="text.secondary" sx={{ p: 2 }} variant="body2">
      {message}
    </Typography>
  );
}
