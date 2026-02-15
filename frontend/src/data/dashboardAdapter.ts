import { hasSupabaseConfig, supabase } from './supabaseClient';
import { mockDashboardData } from './mockData';
import type {
  DashboardData,
  DashboardDailyPoint,
  DatePreset,
  IngestionAuditItem,
  KpiCardData,
  SourceHealth,
  SourceStatusItem,
} from '../types';

type DashboardRow = {
  day: string;
  brutto_kwh: number | null;
  ev_kwh: number | null;
  netto_kwh: number | null;
  hot_water_usage: number | null;
  avg_temperature_c: number | null;
};

type SourceStatusRow = {
  source_name: string;
  checked_at: string;
  status: string;
  message: string | null;
};

type IngestionRunRow = {
  id: number;
  started_at: string;
  finished_at: string | null;
  status: string;
  source_count: number;
  success_count: number;
  failure_count: number;
  details: Record<string, unknown> | null;
};

type DateRange = {
  start: string;
  end: string;
  compareStart: string;
  compareEnd: string;
  rollingStart: string;
};

function formatDay(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function mapPresetToRange(preset: DatePreset): DateRange {
  const endDate = new Date();
  const end = formatDay(endDate);

  const startDate = new Date(endDate);
  if (preset === 'thisMonth') {
    startDate.setDate(1);
  } else if (preset === 'last30Days') {
    startDate.setDate(startDate.getDate() - 29);
  } else {
    startDate.setMonth(startDate.getMonth() - 3);
    startDate.setDate(startDate.getDate() + 1);
  }

  const compareEndDate = new Date(startDate);
  compareEndDate.setDate(compareEndDate.getDate() - 1);

  const spanInDays = Math.max(
    1,
    Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) + 1,
  );

  const compareStartDate = new Date(compareEndDate);
  compareStartDate.setDate(compareStartDate.getDate() - (spanInDays - 1));

  const rollingStartDate = new Date(startDate);
  rollingStartDate.setDate(rollingStartDate.getDate() - 120);

  return {
    start: formatDay(startDate),
    end,
    compareStart: formatDay(compareStartDate),
    compareEnd: formatDay(compareEndDate),
    rollingStart: formatDay(rollingStartDate),
  };
}

function toNumber(value: number | null): number {
  return Number((value ?? 0).toFixed(2));
}

function computeRollingAverage(points: DashboardDailyPoint[]): DashboardDailyPoint[] {
  return points.map((point, index) => {
    const earlier = points.slice(Math.max(0, index - 90), index);
    if (earlier.length < 7) {
      return { ...point, threeMonthAverageKwh: null };
    }

    const avg = earlier.reduce((sum, item) => sum + item.bruttoKwh, 0) / earlier.length;
    return { ...point, threeMonthAverageKwh: Number(avg.toFixed(2)) };
  });
}

function sumMetric(points: DashboardDailyPoint[], metric: keyof DashboardDailyPoint): number {
  return Number(points.reduce((sum, point) => sum + Number(point[metric] ?? 0), 0).toFixed(2));
}

function toDelta(current: number, previous: number): number | null {
  if (previous === 0) {
    return null;
  }

  return Number((((current - previous) / previous) * 100).toFixed(1));
}

function mapHealth(statusValue: string): SourceHealth {
  const normalized = statusValue.trim().toLowerCase();
  if (normalized === 'ok' || normalized === 'healthy' || normalized === 'success') {
    return 'healthy';
  }
  if (normalized === 'warning' || normalized === 'degraded' || normalized === 'partial') {
    return 'warning';
  }
  return 'error';
}

function buildKpis(currentPeriod: DashboardDailyPoint[], previousPeriod: DashboardDailyPoint[]): KpiCardData[] {
  const brutto = sumMetric(currentPeriod, 'bruttoKwh');
  const netto = sumMetric(currentPeriod, 'nettoKwh');
  const ev = sumMetric(currentPeriod, 'evKwh');
  const hotWater = sumMetric(currentPeriod, 'hotWaterUsage');
  const weather =
    currentPeriod.length === 0
      ? 0
      : Number(
          (
            currentPeriod.reduce((sum, point) => sum + point.avgTemperatureC, 0) /
            currentPeriod.length
          ).toFixed(1),
        );

  const prevBrutto = sumMetric(previousPeriod, 'bruttoKwh');
  const prevNetto = sumMetric(previousPeriod, 'nettoKwh');
  const prevEv = sumMetric(previousPeriod, 'evKwh');
  const prevHotWater = sumMetric(previousPeriod, 'hotWaterUsage');

  return [
    { key: 'brutto', label: 'Brutto', value: brutto, unit: 'kWh', deltaPercent: toDelta(brutto, prevBrutto) },
    { key: 'netto', label: 'Netto', value: netto, unit: 'kWh', deltaPercent: toDelta(netto, prevNetto) },
    { key: 'ev', label: 'EV', value: ev, unit: 'kWh', deltaPercent: toDelta(ev, prevEv) },
    {
      key: 'hot_water',
      label: 'Hot Water',
      value: hotWater,
      unit: 'm³',
      deltaPercent: toDelta(hotWater, prevHotWater),
    },
    { key: 'weather', label: 'Weather', value: weather, unit: '°C', deltaPercent: null },
  ];
}

function mapRows(rows: DashboardRow[]): DashboardDailyPoint[] {
  return rows.map((row) => ({
    day: row.day,
    bruttoKwh: toNumber(row.brutto_kwh),
    evKwh: toNumber(row.ev_kwh),
    nettoKwh: toNumber(row.netto_kwh),
    hotWaterUsage: toNumber(row.hot_water_usage),
    avgTemperatureC: toNumber(row.avg_temperature_c),
    threeMonthAverageKwh: null,
  }));
}

function dedupeLatestStatuses(rows: SourceStatusRow[]): SourceStatusItem[] {
  const latestBySource = new Map<string, SourceStatusRow>();

  for (const row of rows) {
    const existing = latestBySource.get(row.source_name);
    if (!existing || row.checked_at > existing.checked_at) {
      latestBySource.set(row.source_name, row);
    }
  }

  return Array.from(latestBySource.values())
    .sort((a, b) => a.source_name.localeCompare(b.source_name))
    .map((row) => ({
      sourceName: row.source_name,
      health: mapHealth(row.status),
      checkedAt: row.checked_at,
      message: row.message,
    }));
}

function mapIngestionRuns(rows: IngestionRunRow[]): IngestionAuditItem[] {
  return rows.map((row) => ({
    id: row.id,
    startedAt: row.started_at,
    finishedAt: row.finished_at,
    status: row.status,
    sourceCount: row.source_count,
    successCount: row.success_count,
    failureCount: row.failure_count,
    details: row.details,
  }));
}

export async function getDashboardData(preset: DatePreset): Promise<DashboardData> {
  if (!hasSupabaseConfig || !supabase) {
    return mockDashboardData;
  }

  const range = mapPresetToRange(preset);

  const [dashboardResult, statusResult, runResult] = await Promise.all([
    supabase
      .schema('energy')
      .from('dashboard_daily')
      .select('day,brutto_kwh,ev_kwh,netto_kwh,hot_water_usage,avg_temperature_c')
      .gte('day', range.rollingStart)
      .lte('day', range.end)
      .order('day', { ascending: true }),
    supabase
      .schema('energy')
      .from('source_status')
      .select('source_name,checked_at,status,message')
      .order('checked_at', { ascending: false })
      .limit(100),
    supabase
      .schema('energy')
      .from('ingestion_runs')
      .select('id,started_at,finished_at,status,source_count,success_count,failure_count,details')
      .order('started_at', { ascending: false })
      .limit(20),
  ]);

  if (dashboardResult.error) {
    throw new Error(`Failed to load dashboard_daily: ${dashboardResult.error.message}`);
  }
  if (statusResult.error) {
    throw new Error(`Failed to load source_status: ${statusResult.error.message}`);
  }
  if (runResult.error) {
    throw new Error(`Failed to load ingestion_runs: ${runResult.error.message}`);
  }

  const allRows = mapRows((dashboardResult.data ?? []) as DashboardRow[]);
  const currentPeriod = allRows.filter((row) => row.day >= range.start && row.day <= range.end);
  const previousPeriod = allRows.filter(
    (row) => row.day >= range.compareStart && row.day <= range.compareEnd,
  );

  const currentWithAverage = computeRollingAverage(currentPeriod);

  return {
    kpis: buildKpis(currentPeriod, previousPeriod),
    energySeries: currentWithAverage,
    hotWaterSeries: currentWithAverage,
    evSeries: currentWithAverage,
    sourceStatus: dedupeLatestStatuses((statusResult.data ?? []) as SourceStatusRow[]),
    ingestionAudit: mapIngestionRuns((runResult.data ?? []) as IngestionRunRow[]),
    hasAnyData: currentWithAverage.length > 0,
    lastUpdatedAt: new Date().toISOString(),
  };
}
