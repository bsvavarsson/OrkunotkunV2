import type { ReactElement } from 'react';
import type { KpiCardData } from '../types';

type Props = {
  item: KpiCardData;
};

function formatNumber(value: number): string {
  return new Intl.NumberFormat('is-IS', { maximumFractionDigits: 1 }).format(value);
}

export function KpiCard({ item }: Props): ReactElement {
  const delta = item.deltaPercent;
  const deltaTone = delta === null ? 'neutral' : delta > 0 ? 'up' : delta < 0 ? 'down' : 'neutral';
  const deltaPrefix = delta !== null && delta > 0 ? '+' : '';

  return (
    <section className="panel kpi-card" aria-label={item.label}>
      <p className="kpi-label">{item.label}</p>
      <p className="kpi-value">
        {formatNumber(item.value)} <span className="kpi-unit">{item.unit}</span>
      </p>
      <p className={`kpi-delta ${deltaTone}`}>
        {delta === null ? '—' : `${deltaPrefix}${formatNumber(delta)}% vs fyrra tímabil`}
      </p>
    </section>
  );
}
