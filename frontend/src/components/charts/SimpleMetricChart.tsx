import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ReactElement } from 'react';
import type { DashboardDailyPoint } from '../../types';

type Props = {
  points: DashboardDailyPoint[];
  metric: 'hotWaterUsage' | 'evKwh';
  unit: string;
};

function formatDay(day: string): string {
  return new Intl.DateTimeFormat('is-IS', { day: '2-digit', month: '2-digit' }).format(new Date(day));
}

export function SimpleMetricChart({ points, metric, unit }: Props): ReactElement {
  return (
    <div className="chart-wrap" role="img" aria-label="Sögulegt línurit">
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 6 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="day" tickFormatter={formatDay} minTickGap={20} />
          <YAxis unit={` ${unit}`} width={58} />
          <Tooltip
            labelFormatter={(value) =>
              new Intl.DateTimeFormat('is-IS', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              }).format(new Date(String(value)))
            }
          />
          <Area
            type="monotone"
            dataKey={metric}
            stroke="var(--line-primary)"
            fill="var(--area-fill)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
