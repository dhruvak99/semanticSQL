import DashboardIcon from '@mui/icons-material/Dashboard';
import SearchIcon from '@mui/icons-material/Search';
import StorageIcon from '@mui/icons-material/Storage';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import InsightsIcon from '@mui/icons-material/Insights';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import HistoryIcon from '@mui/icons-material/History';
import SchemaIcon from '@mui/icons-material/Schema';
import ScienceIcon from '@mui/icons-material/Science';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import MemoryIcon from '@mui/icons-material/Memory';
import SettingsIcon from '@mui/icons-material/Settings';
import type { SvgIconComponent } from '@mui/icons-material';
import type { ComponentType } from 'react';
import { DashboardPage } from '../pages/DashboardPage';
import { QueryInterfacePage } from '../pages/QueryInterfacePage';
import { SemanticCachePage } from '../pages/SemanticCachePage';
import { DatabaseExplorerPage } from '../pages/DatabaseExplorerPage';
import { QueryAnalyticsPage } from '../pages/QueryAnalyticsPage';
import { ValidationCorrectionPage } from '../pages/ValidationCorrectionPage';
import { QueryHistoryPage } from '../pages/QueryHistoryPage';
import { SchemaManagerPage } from '../pages/SchemaManagerPage';
import { ResearchDashboardPage } from '../pages/ResearchDashboardPage';
import { SystemMonitorPage } from '../pages/SystemMonitorPage';
import { ModelManagementPage } from '../pages/ModelManagementPage';
import { SettingsPage } from '../pages/SettingsPage';

export type AppRoute = {
  path: string;
  label: string;
  description: string;
  icon: SvgIconComponent;
  element: ComponentType;
};

export const routes: AppRoute[] = [
  { path: '/', label: 'Dashboard', description: 'Operational overview for SemanticSQL.', icon: DashboardIcon, element: DashboardPage },
  { path: '/query', label: 'Query Interface', description: 'Natural language query workspace.', icon: SearchIcon, element: QueryInterfacePage },
  { path: '/semantic-cache', label: 'Semantic Cache', description: 'Redis-backed cache visibility.', icon: StorageIcon, element: SemanticCachePage },
  { path: '/database-explorer', label: 'Database Explorer', description: 'Inspect connected relational databases.', icon: AccountTreeIcon, element: DatabaseExplorerPage },
  { path: '/query-analytics', label: 'Query Analytics', description: 'Query performance and usage patterns.', icon: InsightsIcon, element: QueryAnalyticsPage },
  { path: '/validation-correction', label: 'Validation & Correction', description: 'SQL validation and correction workflow.', icon: FactCheckIcon, element: ValidationCorrectionPage },
  { path: '/query-history', label: 'Query History', description: 'Past prompts, generated SQL, and outcomes.', icon: HistoryIcon, element: QueryHistoryPage },
  { path: '/schema-manager', label: 'Schema Manager', description: 'Manage schema metadata and relationships.', icon: SchemaIcon, element: SchemaManagerPage },
  { path: '/research-dashboard', label: 'Research Dashboard', description: 'Model and experiment research workspace.', icon: ScienceIcon, element: ResearchDashboardPage },
  { path: '/system-monitor', label: 'System Monitor', description: 'Service health and infrastructure signals.', icon: MonitorHeartIcon, element: SystemMonitorPage },
  { path: '/model-management', label: 'Model Management', description: 'Embedding and language model configuration.', icon: MemoryIcon, element: ModelManagementPage },
  { path: '/settings', label: 'Settings', description: 'Application and connection preferences.', icon: SettingsIcon, element: SettingsPage }
];
