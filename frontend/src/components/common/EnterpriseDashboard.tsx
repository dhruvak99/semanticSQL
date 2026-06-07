import type { ReactNode } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  LinearProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from '@mui/material';
import type { SvgIconComponent } from '@mui/icons-material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

export type Tone = 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'cyan' | 'gray';

const toneMap: Record<Tone, { main: string; soft: string; text: string }> = {
  blue: { main: '#2563eb', soft: '#eaf1ff', text: '#1d4ed8' },
  green: { main: '#16a34a', soft: '#e9f8ef', text: '#15803d' },
  orange: { main: '#f59e0b', soft: '#fff5df', text: '#b45309' },
  red: { main: '#ef4444', soft: '#ffeded', text: '#b91c1c' },
  purple: { main: '#7c3aed', soft: '#f1eaff', text: '#6d28d9' },
  cyan: { main: '#0891b2', soft: '#e6f8fb', text: '#0e7490' },
  gray: { main: '#64748b', soft: '#f1f5f9', text: '#475569' }
};

export type StatCardProps = {
  label: string;
  value: string;
  helper?: string;
  trend?: string;
  trendDirection?: 'up' | 'down';
  tone?: Tone;
  icon: SvgIconComponent;
};

export function StatCard({
  label,
  value,
  helper,
  trend,
  trendDirection = 'up',
  tone = 'blue',
  icon: Icon
}: StatCardProps) {
  const colors = toneMap[tone];
  const TrendIcon = trendDirection === 'up' ? TrendingUpIcon : TrendingDownIcon;

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" spacing={2} sx={{ alignItems: 'flex-start' }}>
          <Box
            sx={{
              width: 46,
              height: 46,
              borderRadius: 2,
              display: 'grid',
              placeItems: 'center',
              color: colors.main,
              bgcolor: colors.soft
            }}
          >
            <Icon />
          </Box>
          <Box sx={{ minWidth: 0 }}>
            <Typography color="text.secondary" fontWeight={700} variant="caption">
              {label}
            </Typography>
            <Typography sx={{ mt: 0.5 }} variant="h4">
              {value}
            </Typography>
            {helper ? (
              <Typography color="text.secondary" variant="body2">
                {helper}
              </Typography>
            ) : null}
            {trend ? (
              <Stack direction="row" spacing={0.5} sx={{ mt: 1, alignItems: 'center', color: trendDirection === 'up' ? 'success.main' : 'error.main' }}>
                <TrendIcon sx={{ fontSize: 16 }} />
                <Typography fontWeight={700} variant="caption">
                  {trend}
                </Typography>
              </Stack>
            ) : null}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

type PanelProps = {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  minHeight?: number;
};

export function Panel({ title, subtitle, action, children, minHeight }: PanelProps) {
  return (
    <Card sx={{ height: '100%', minHeight }}>
      <CardContent>
        <Stack direction="row" sx={{ alignItems: 'flex-start', justifyContent: 'space-between', gap: 2, mb: 2 }}>
          <Box>
            <Typography variant="h6">{title}</Typography>
            {subtitle ? (
              <Typography color="text.secondary" variant="body2">
                {subtitle}
              </Typography>
            ) : null}
          </Box>
          {action}
        </Stack>
        {children}
      </CardContent>
    </Card>
  );
}

type LineChartProps = {
  data: number[];
  labels?: string[];
  color?: string;
  secondaryData?: number[];
  secondaryColor?: string;
  height?: number;
};

export function LineChart({ data, labels, color = '#2563eb', secondaryData, secondaryColor = '#16a34a', height = 220 }: LineChartProps) {
  const width = 720;
  const padding = 34;
  const allValues = secondaryData ? [...data, ...secondaryData] : data;
  const max = Math.max(...allValues) * 1.12;
  const min = Math.min(0, ...allValues);
  const scaleX = (index: number, length: number) => padding + (index * (width - padding * 2)) / Math.max(length - 1, 1);
  const scaleY = (value: number) => height - padding - ((value - min) / Math.max(max - min, 1)) * (height - padding * 2);
  const points = (values: number[]) => values.map((value, index) => `${scaleX(index, values.length)},${scaleY(value)}`).join(' ');

  return (
    <Box sx={{ width: '100%', overflow: 'hidden' }}>
      <svg aria-label="line chart" role="img" viewBox={`0 0 ${width} ${height}`} width="100%" height={height}>
        {[0, 1, 2, 3].map((tick) => {
          const y = padding + tick * ((height - padding * 2) / 3);
          return <line key={tick} x1={padding} x2={width - padding} y1={y} y2={y} stroke="#e8edf5" />;
        })}
        <polyline fill="none" points={points(data)} stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" />
        {secondaryData ? (
          <polyline fill="none" points={points(secondaryData)} stroke={secondaryColor} strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" />
        ) : null}
        {data.map((value, index) => (
          <circle key={`${value}-${index}`} cx={scaleX(index, data.length)} cy={scaleY(value)} fill={color} r="5" />
        ))}
        {labels?.map((label, index) => (
          <text key={label} fill="#64748b" fontSize="12" textAnchor="middle" x={scaleX(index, labels.length)} y={height - 8}>
            {label}
          </text>
        ))}
      </svg>
    </Box>
  );
}

type DonutChartProps = {
  segments: Array<{ label: string; value: number; color: string }>;
  centerLabel?: string;
};

export function DonutChart({ segments, centerLabel }: DonutChartProps) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);
  let offset = 25;

  return (
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} sx={{ alignItems: 'center' }}>
      <Box sx={{ position: 'relative', width: 172, height: 172, flexShrink: 0 }}>
        <svg viewBox="0 0 42 42" width="172" height="172">
          <circle cx="21" cy="21" fill="transparent" r="15.915" stroke="#e5eaf1" strokeWidth="7" />
          {segments.map((segment) => {
            const dash = (segment.value / total) * 100;
            const circle = (
              <circle
                key={segment.label}
                cx="21"
                cy="21"
                fill="transparent"
                r="15.915"
                stroke={segment.color}
                strokeDasharray={`${dash} ${100 - dash}`}
                strokeDashoffset={offset}
                strokeWidth="7"
              />
            );
            offset -= dash;
            return circle;
          })}
        </svg>
        {centerLabel ? (
          <Stack sx={{ position: 'absolute', inset: 0, alignItems: 'center', justifyContent: 'center' }}>
            <Typography variant="h6">{centerLabel}</Typography>
            <Typography color="text.secondary" variant="caption">
              Total
            </Typography>
          </Stack>
        ) : null}
      </Box>
      <Stack spacing={1} sx={{ minWidth: 180 }}>
        {segments.map((segment) => (
          <Stack key={segment.label} direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
              <Box sx={{ width: 10, height: 10, borderRadius: 1, bgcolor: segment.color }} />
              <Typography variant="body2">{segment.label}</Typography>
            </Stack>
            <Typography fontWeight={700} variant="body2">
              {segment.value}%
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Stack>
  );
}

type BarChartProps = {
  data: Array<{ label: string; value: number; color?: string }>;
  max?: number;
};

export function BarChart({ data, max }: BarChartProps) {
  const largest = max ?? Math.max(...data.map((item) => item.value));

  return (
    <Stack spacing={1.5}>
      {data.map((item) => (
        <Grid container key={item.label} spacing={1.5} sx={{ alignItems: 'center' }}>
          <Grid item xs={4}>
            <Typography variant="body2">{item.label}</Typography>
          </Grid>
          <Grid item xs={6}>
            <LinearProgress
              value={(item.value / largest) * 100}
              variant="determinate"
              sx={{
                height: 12,
                borderRadius: 999,
                bgcolor: '#eef2f7',
                '& .MuiLinearProgress-bar': {
                  bgcolor: item.color ?? '#2563eb',
                  borderRadius: 999
                }
              }}
            />
          </Grid>
          <Grid item xs={2}>
            <Typography fontWeight={700} textAlign="right" variant="body2">
              {item.value}
            </Typography>
          </Grid>
        </Grid>
      ))}
    </Stack>
  );
}

export function StatusBadge({ label, tone = 'green' }: { label: string; tone?: Tone }) {
  const colors = toneMap[tone];
  return (
    <Chip
      label={label}
      size="small"
      sx={{
        bgcolor: colors.soft,
        color: colors.text,
        border: `1px solid ${colors.main}33`,
        fontWeight: 700
      }}
    />
  );
}

export function MetricProgress({ label, value, detail, tone = 'blue' }: { label: string; value: number; detail?: string; tone?: Tone }) {
  const colors = toneMap[tone];
  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 0.75 }}>
        <Typography variant="body2">{label}</Typography>
        <Typography fontWeight={700} variant="body2">
          {value}%
        </Typography>
      </Stack>
      <LinearProgress
        value={value}
        variant="determinate"
        sx={{
          height: 9,
          borderRadius: 999,
          bgcolor: '#eef2f7',
          '& .MuiLinearProgress-bar': { bgcolor: colors.main, borderRadius: 999 }
        }}
      />
      {detail ? (
        <Typography color="text.secondary" sx={{ mt: 0.5 }} variant="caption">
          {detail}
        </Typography>
      ) : null}
    </Box>
  );
}

type DataTableProps = {
  columns: string[];
  rows: Array<Array<ReactNode>>;
  dense?: boolean;
};

export function DataTable({ columns, rows, dense = true }: DataTableProps) {
  return (
    <TableContainer>
      <Table size={dense ? 'small' : 'medium'}>
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell key={column}>{column}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row, rowIndex) => (
            <TableRow key={rowIndex} hover>
              {row.map((cell, cellIndex) => (
                <TableCell key={`${rowIndex}-${cellIndex}`}>{cell}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export function CodeBlock({ code, dark = false }: { code: string; dark?: boolean }) {
  return (
    <Box
      component="pre"
      sx={{
        m: 0,
        p: 2,
        overflow: 'auto',
        minHeight: 96,
        borderRadius: 1,
        border: '1px solid',
        borderColor: dark ? '#1e293b' : 'divider',
        bgcolor: dark ? '#071525' : '#fbfdff',
        color: dark ? '#e2e8f0' : '#172033',
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
        fontSize: 13,
        lineHeight: 1.7,
        whiteSpace: 'pre-wrap'
      }}
    >
      {code}
    </Box>
  );
}

export function FilterBar({ items, primaryLabel = 'Apply Filters' }: { items: string[]; primaryLabel?: string }) {
  return (
    <Card>
      <CardContent>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
          {items.map((item) => (
            <Button key={item} color="inherit" variant="outlined">
              {item}
            </Button>
          ))}
          <Box sx={{ flexGrow: 1 }} />
          <Button variant="outlined">Reset</Button>
          <Button>{primaryLabel}</Button>
        </Stack>
      </CardContent>
    </Card>
  );
}

export function Heatmap({ rows, columns }: { rows: string[]; columns: string[] }) {
  return (
    <Box sx={{ overflowX: 'auto' }}>
      <Grid container columns={columns.length + 1} sx={{ minWidth: 520 }}>
        <Grid item xs={1} />
        {columns.map((column) => (
          <Grid item key={column} xs={1}>
            <Typography color="text.secondary" textAlign="center" variant="caption">
              {column}
            </Typography>
          </Grid>
        ))}
        {rows.map((row, rowIndex) => (
          <Grid container columns={columns.length + 1} key={row}>
            <Grid item xs={1}>
              <Typography color="text.secondary" variant="caption">
                {row}
              </Typography>
            </Grid>
            {columns.map((column, columnIndex) => {
              const intensity = Math.round(20 + ((rowIndex + 2) * (columnIndex + 3) * 11) % 78);
              return (
                <Grid item key={`${row}-${column}`} xs={1}>
                  <Box sx={{ height: 24, m: 0.25, borderRadius: 0.5, bgcolor: `rgba(37, 99, 235, ${intensity / 100})` }} />
                </Grid>
              );
            })}
          </Grid>
        ))}
      </Grid>
      <Divider sx={{ my: 1.5 }} />
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
        <Typography color="text.secondary" variant="caption">
          Low
        </Typography>
        <Box sx={{ width: 160, height: 8, borderRadius: 999, background: 'linear-gradient(90deg, #dbeafe, #2563eb)' }} />
        <Typography color="text.secondary" variant="caption">
          High
        </Typography>
      </Stack>
    </Box>
  );
}

export function DashboardActions({ labels }: { labels: string[] }) {
  return (
    <Stack direction="row" spacing={1}>
      {labels.map((label, index) => (
        <Button key={label} variant={index === labels.length - 1 ? 'contained' : 'outlined'}>
          {label}
        </Button>
      ))}
    </Stack>
  );
}
