export type DatePreset = 'thisMonth' | 'last30Days' | 'last3Months';

export type DashboardDailyPoint = {
  day: string;
  bruttoKwh: number;
  evKwh: number;
  nettoKwh: number;
  hotWaterUsage: number;
  avgTemperatureC: number;
  threeMonthAverageKwh: number | null;
};

export type KpiCardData = {
  key: 'brutto' | 'netto' | 'ev' | 'hot_water' | 'weather';
  label: string;
  value: number;
  unit: string;
  deltaPercent: number | null;
};

export type SourceHealth = 'healthy' | 'warning' | 'error';

export type SourceStatusItem = {
  sourceName: string;
  health: SourceHealth;
  checkedAt: string;
  message: string | null;
};

export type IngestionAuditItem = {
  id: number;
  startedAt: string;
  finishedAt: string | null;
  status: string;
  sourceCount: number;
  successCount: number;
  failureCount: number;
  details: Record<string, unknown> | null;
};

export type DashboardData = {
  kpis: KpiCardData[];
  energySeries: DashboardDailyPoint[];
  hotWaterSeries: DashboardDailyPoint[];
  evSeries: DashboardDailyPoint[];
  sourceStatus: SourceStatusItem[];
  ingestionAudit: IngestionAuditItem[];
  hasAnyData: boolean;
  lastUpdatedAt: string;
};
