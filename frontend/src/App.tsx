import { Fragment, type ReactElement, useEffect, useMemo, useState } from 'react';
import { EnergyChart } from './components/charts/EnergyChart';
import { SimpleMetricChart } from './components/charts/SimpleMetricChart';
import { KpiCard } from './components/KpiCard';
import { Panel } from './components/Panel';
import { getDashboardData } from './data/dashboardAdapter';
import { hasSupabaseConfig } from './data/supabaseClient';
import type { DashboardData, DatePreset, IngestionAuditItem, SourceStatusItem } from './types';

const presetOptions: Array<{ value: DatePreset; label: string }> = [
  { value: 'thisMonth', label: 'Þessi mánuður' },
  { value: 'last30Days', label: 'Síðustu 30 dagar' },
  { value: 'last3Months', label: 'Síðustu 3 mánuðir' },
];

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat('is-IS', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Atlantic/Reykjavik',
  }).format(new Date(value));
}

function formatStatus(status: string): string {
  return status.replaceAll('_', ' ');
}

function statusText(item: SourceStatusItem): string {
  if (item.health === 'healthy') {
    return 'Healthy';
  }
  if (item.health === 'warning') {
    return 'Warning';
  }
  return 'Error';
}

function statusClass(item: SourceStatusItem): string {
  return `status-dot ${item.health}`;
}

function auditDuration(item: IngestionAuditItem): string {
  if (!item.finishedAt) {
    return '—';
  }
  const durationMs = new Date(item.finishedAt).getTime() - new Date(item.startedAt).getTime();
  if (durationMs <= 0) {
    return '—';
  }

  const seconds = Math.round(durationMs / 1000);
  return `${seconds}s`;
}

export default function App(): ReactElement {
  const [preset, setPreset] = useState<DatePreset>('thisMonth');
  const [expandedAuditId, setExpandedAuditId] = useState<number | null>(null);
  const [state, setState] = useState<{
    loading: boolean;
    error: string | null;
    data: DashboardData | null;
  }>({
    loading: true,
    error: null,
    data: null,
  });

  useEffect(() => {
    let active = true;

    setState((prev) => ({ ...prev, loading: true, error: null }));

    getDashboardData(preset)
      .then((data) => {
        if (!active) {
          return;
        }
        setState({ loading: false, error: null, data });
      })
      .catch((error: Error) => {
        if (!active) {
          return;
        }
        setState({ loading: false, error: error.message, data: null });
      });

    return () => {
      active = false;
    };
  }, [preset]);

  const subtitle = useMemo(() => {
    if (!state.data) {
      return '';
    }
    return `Síðast uppfært: ${formatDateTime(state.data.lastUpdatedAt)}`;
  }, [state.data]);

  return (
    <main className="dashboard-root">
      <header className="topbar">
        <div>
          <h1>Orkunotkun</h1>
          <p className="topbar-subtitle">Home Energy Consumption Dashboard</p>
        </div>
        <div className="topbar-controls">
          {!hasSupabaseConfig ? <span className="pill">Demo gögn</span> : null}
          <label className="range-control">
            <span>Tímabil</span>
            <select value={preset} onChange={(event) => setPreset(event.target.value as DatePreset)}>
              {presetOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      {state.error ? (
        <div className="alert error">
          <p>Ekki tókst að sækja mælaborðsgögn.</p>
          <p>{state.error}</p>
        </div>
      ) : null}

      {state.loading ? (
        <div className="loading-grid" aria-live="polite" aria-busy="true">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={`kpi-${String(index)}`} className="skeleton kpi-skeleton" />
          ))}
          <div className="skeleton chart-skeleton" />
          <div className="skeleton panel-skeleton" />
          <div className="skeleton panel-skeleton" />
          <div className="skeleton panel-skeleton" />
          <div className="skeleton table-skeleton" />
        </div>
      ) : null}

      {!state.loading && state.data && !state.data.hasAnyData ? (
        <div className="alert info">
          <p>Engin gögn fundust fyrir valið tímabil.</p>
          <p>Prófaðu annað tímabil eða keyrðu nýja ingestion run.</p>
        </div>
      ) : null}

      {!state.loading && state.data && state.data.hasAnyData ? (
        <section className="dashboard-grid">
          <div className="kpi-row">
            {state.data.kpis.map((item) => (
              <KpiCard key={item.key} item={item} />
            ))}
          </div>

          <div className="chart-row">
            <Panel title="Energy Consumption per Day" subtitle={subtitle}>
              <EnergyChart points={state.data.energySeries} />
            </Panel>

            <Panel title="Hot Water (Last 3 Months)">
              <SimpleMetricChart points={state.data.hotWaterSeries} metric="hotWaterUsage" unit="m³" />
            </Panel>

            <Panel title="EV Charging (Last 3 Months)">
              <SimpleMetricChart points={state.data.evSeries} metric="evKwh" unit="kWh" />
            </Panel>
          </div>

          <Panel title="Source Status">
            <ul className="source-list">
              {state.data.sourceStatus.map((item) => (
                <li key={item.sourceName} className="source-item">
                  <div className="source-row">
                    <div className="source-main">
                      <span className={statusClass(item)} aria-hidden="true" />
                      <div>
                        <p className="source-name">{item.sourceName}</p>
                        <p className="source-time">{formatDateTime(item.checkedAt)}</p>
                      </div>
                    </div>
                    <p className="source-state">{statusText(item)}</p>
                  </div>
                  {item.message ? <p className="source-message">{item.message}</p> : null}
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="Ingestion Audit Logs">
            <div className="audit-table-wrap">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Run Time</th>
                    <th>Status</th>
                    <th>Rows</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {state.data.ingestionAudit.map((row) => {
                    const isExpanded = expandedAuditId === row.id;
                    return (
                      <Fragment key={row.id}>
                        <tr
                          className="audit-row"
                          onClick={() => setExpandedAuditId((prev) => (prev === row.id ? null : row.id))}
                        >
                          <td>{formatDateTime(row.startedAt)}</td>
                          <td>{formatStatus(row.status)}</td>
                          <td>
                            {row.successCount}/{row.sourceCount}
                          </td>
                          <td>{auditDuration(row)}</td>
                        </tr>
                        {isExpanded ? (
                          <tr className="audit-row-expanded">
                            <td colSpan={4}>
                              <pre>{JSON.stringify(row.details ?? {}, null, 2)}</pre>
                            </td>
                          </tr>
                        ) : null}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Panel>
        </section>
      ) : null}
    </main>
  );
}
