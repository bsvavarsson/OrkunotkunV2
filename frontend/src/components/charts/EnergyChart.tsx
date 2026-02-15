import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import type { ReactElement } from 'react';
import type { DashboardDailyPoint } from '../../types';

type Props = {
  points: DashboardDailyPoint[];
};

function formatDay(day: string): string {
  return new Intl.DateTimeFormat('is-IS', { day: '2-digit', month: '2-digit' }).format(new Date(day));
}

export function EnergyChart({ points }: Props): ReactElement {
  return (
    <div className="chart-wrap" role="img" aria-label="Dagleg orkunotkun og 3 mánaða meðaltal">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={points} margin={{ top: 12, right: 16, left: 6, bottom: 6 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="day" tickFormatter={formatDay} minTickGap={24} />
          <YAxis unit=" kWh" width={70} />
          <Tooltip
            labelFormatter={(value) =>
              new Intl.DateTimeFormat('is-IS', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              }).format(new Date(String(value)))
            }
          />
          <Line
            type="monotone"
            dataKey="bruttoKwh"
            name="Brutto"
            stroke="var(--line-primary)"
            strokeWidth={2.5}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="threeMonthAverageKwh"
            name="3 mánaða meðaltal"
            stroke="var(--line-muted)"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
