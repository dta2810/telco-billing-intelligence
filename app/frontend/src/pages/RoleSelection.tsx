import { Link } from 'react-router-dom';
import { Activity, Users } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { useI18n, withLang } from '../i18n';

interface SmokeData {
  table_counts: Record<string, number>;
  metric_view_arpu_last_period: { arpu: string; revenue: string } | null;
}

export function RoleSelection() {
  const { t, lang } = useI18n();
  const { data, loading } = useApi<SmokeData>(withLang('/api/smoke', lang));

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-semibold mb-2">AcmeTel Billing Intelligence</h1>
        <p className="text-db-muted">{t('role.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        <Link
          to="/exec"
          className="bg-db-card border border-db-border hover:border-db-accent rounded-lg p-6 transition-colors group"
        >
          <Activity className="text-db-accent mb-3" size={28} />
          <h2 className="text-lg font-semibold mb-1">{t('role.exec.title')}</h2>
          <p className="text-sm text-db-muted">{t('role.exec.desc')}</p>
        </Link>

        <Link
          to="/customer"
          className="bg-db-card border border-db-border hover:border-db-accent rounded-lg p-6 transition-colors group"
        >
          <Users className="text-db-accent mb-3" size={28} />
          <h2 className="text-lg font-semibold mb-1">{t('role.customer.title')}</h2>
          <p className="text-sm text-db-muted">{t('role.customer.desc')}</p>
        </Link>
      </div>

      {/* Smoke status */}
      <div className="text-xs text-db-muted border-t border-db-border pt-4">
        {loading ? (
          t('role.connecting')
        ) : data ? (
          <span>
            ✓ {t('role.connectedTo')}{' '}
            {Object.entries(data.table_counts)
              .map(([tb, n]) => `${tb}: ${n.toLocaleString()}`)
              .join(' · ')}
            {data.metric_view_arpu_last_period && (
              <> · {t('role.arpuLast')}: ${parseFloat(data.metric_view_arpu_last_period.arpu).toFixed(2)}</>
            )}
          </span>
        ) : (
          <span className="text-db-red">{t('role.notConnected')}</span>
        )}
      </div>
    </div>
  );
}
