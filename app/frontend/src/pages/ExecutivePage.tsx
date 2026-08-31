import { useApi } from '../hooks/useApi';
import { KpiTile, KpiTileData } from '../components/KpiTile';
import { AiInsights } from '../components/AiInsights';
import { ArpuTrend } from '../components/ArpuTrend';
import { DunningChart } from '../components/DunningChart';
import { CohortExplorer } from '../components/CohortExplorer';
import { useI18n, withLang } from '../i18n';

interface KpiResponse {
  period: string;
  tiles: KpiTileData[];
}

interface InsightsResponse {
  period: string;
  narrative: string;
  structured: {
    arpu_trend: { billing_period: string; arpu: number; revenue: number }[];
    dunning_distribution: { dunning_stage: number; pagos: number; clientes: number }[];
    overage_by_plan: { plan_name: string; rate: number; subs: number }[];
    kpis: Record<string, any>;
  };
}

export function ExecutivePage() {
  const { t, lang } = useI18n();
  const kpis = useApi<KpiResponse>(withLang('/api/exec/kpis', lang));
  const insights = useApi<InsightsResponse>(withLang('/api/exec/insights', lang));

  const formatPeriod = (p: string): string => {
    if (!p || !/^\d{4}-\d{2}$/.test(p)) return p;
    const [y, m] = p.split('-');
    return `${t('month.' + parseInt(m, 10))} ${y}`;
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('exec.title')}</h1>
          <p className="text-db-muted text-sm mt-1">
            {t('exec.subtitle', { period: kpis.data ? formatPeriod(kpis.data.period) : '—' })}
          </p>
        </div>
      </div>

      {/* KPI tiles */}
      {kpis.loading && <div className="text-db-muted text-sm">{t('common.loadingKpis')}</div>}
      {kpis.error && <div className="text-db-red text-sm">{t('common.error')}: {kpis.error}</div>}
      {kpis.data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {kpis.data.tiles.map((t) => (
            <KpiTile key={t.id} tile={t} />
          ))}
        </div>
      )}

      {/* AI Insights */}
      <AiInsights narrative={insights.data?.narrative || null} loading={insights.loading} />

      {/* Charts */}
      {insights.data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ArpuTrend data={insights.data.structured.arpu_trend} />
          <DunningChart data={insights.data.structured.dunning_distribution} />
        </div>
      )}

      {/* Cohort explorer + Genie scoped */}
      <CohortExplorer />
    </div>
  );
}
