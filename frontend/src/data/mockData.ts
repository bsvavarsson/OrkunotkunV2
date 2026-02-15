import type { DashboardData } from '../types';

const today = new Date();

function formatDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function getPoint(daysAgo: number): string {
  const date = new Date(today);
  date.setDate(date.getDate() - daysAgo);
  return formatDate(date);
}

function formatWeatherTimestamp(day: string): string {
  const date = new Date(`${day}T00:00:00Z`);
  return new Intl.DateTimeFormat('is-IS', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'Atlantic/Reykjavik',
  }).format(date);
}

const energySeries = Array.from({ length: 30 }, (_, index) => {
  const reverseIndex = 29 - index;
  const bruttoKwh = 72 + Math.sin(reverseIndex / 4) * 8 + (reverseIndex % 5);
  const evKwh = 8 + Math.cos(reverseIndex / 5) * 3;
  const hotWaterUsage = 1.7 + Math.sin(reverseIndex / 7) * 0.3;
  const nettoKwh = bruttoKwh - evKwh;

  return {
    day: getPoint(reverseIndex),
    bruttoKwh: Number(bruttoKwh.toFixed(2)),
    evKwh: Number(evKwh.toFixed(2)),
    nettoKwh: Number(nettoKwh.toFixed(2)),
    hotWaterUsage: Number(hotWaterUsage.toFixed(2)),
    avgTemperatureC: Number((2 + Math.sin(reverseIndex / 8) * 3).toFixed(2)),
    threeMonthAverageKwh: 69.4,
  };
});

function computePeriodSum(metric: 'bruttoKwh' | 'nettoKwh' | 'evKwh' | 'hotWaterUsage'): number {
  return Number(energySeries.reduce((sum, item) => sum + item[metric], 0).toFixed(2));
}

const latestWeatherPoint = energySeries[energySeries.length - 1];

export const mockDashboardData: DashboardData = {
  kpis: [
    {
      key: 'brutto',
      label: 'Brutto',
      value: computePeriodSum('bruttoKwh'),
      unit: 'kWh',
      deltaPercent: -2.8,
    },
    {
      key: 'netto',
      label: 'Netto',
      value: computePeriodSum('nettoKwh'),
      unit: 'kWh',
      deltaPercent: -1.9,
    },
    {
      key: 'ev',
      label: 'EV',
      value: computePeriodSum('evKwh'),
      unit: 'kWh',
      deltaPercent: 3.6,
    },
    {
      key: 'hot_water',
      label: 'Hot Water',
      value: computePeriodSum('hotWaterUsage'),
      unit: 'm³',
      deltaPercent: 0.7,
    },
    {
      key: 'weather',
      label: `Weather (${formatWeatherTimestamp(latestWeatherPoint.day)})`,
      value: Number(latestWeatherPoint.avgTemperatureC.toFixed(1)),
      unit: '°C',
      deltaPercent: null,
    },
  ],
  energySeries,
  hotWaterSeries: energySeries,
  evSeries: energySeries,
  sourceStatus: [
    {
      sourceName: 'HS Veitur',
      health: 'healthy',
      checkedAt: new Date().toISOString(),
      message: null,
    },
    {
      sourceName: 'Veitur',
      health: 'healthy',
      checkedAt: new Date().toISOString(),
      message: null,
    },
    {
      sourceName: 'Zaptec',
      health: 'warning',
      checkedAt: new Date().toISOString(),
      message: 'Returned rows outside requested range in latest run.',
    },
    {
      sourceName: 'Open-Meteo',
      health: 'healthy',
      checkedAt: new Date().toISOString(),
      message: null,
    },
  ],
  ingestionAudit: [
    {
      id: 111,
      startedAt: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
      finishedAt: new Date(Date.now() - 1000 * 60 * 6).toISOString(),
      status: 'completed',
      sourceCount: 4,
      successCount: 4,
      failureCount: 0,
      details: null,
    },
    {
      id: 110,
      startedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
      finishedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 + 1000 * 60 * 4).toISOString(),
      status: 'completed',
      sourceCount: 4,
      successCount: 3,
      failureCount: 1,
      details: { warning: 'Zaptec returned partial window overlap.' },
    },
  ],
  hasAnyData: true,
  lastUpdatedAt: new Date().toISOString(),
};
