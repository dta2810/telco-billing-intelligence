import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { Gift, AlertTriangle, ClipboardList, ArrowRightLeft, Bell, ChevronDown, ChevronUp, MapPin } from 'lucide-react';
import { useI18n, withLang } from '../i18n';

export interface Alert {
  id: string;
  category: 'promo' | 'disruption' | 'policy' | 'catalog' | 'daily';
  severity: 'good' | 'info' | 'warn' | 'alert';
  title: string;
  body: string;
  region: string | null;
  valid_from: string;
  valid_to: string | null;
  action_label: string | null;
}

const CATEGORY_ICON: Record<Alert['category'], any> = {
  promo: Gift,
  disruption: AlertTriangle,
  policy: ClipboardList,
  catalog: ArrowRightLeft,
  daily: Bell,
};

const SEVERITY_STYLES: Record<Alert['severity'], { border: string; chip: string; icon: string }> = {
  good:  { border: 'border-db-green/40',  chip: 'bg-db-green/10 text-db-green',     icon: 'text-db-green' },
  info:  { border: 'border-blue-400/40',  chip: 'bg-blue-400/10 text-blue-400',     icon: 'text-blue-400' },
  warn:  { border: 'border-db-yellow/40', chip: 'bg-db-yellow/10 text-db-yellow',   icon: 'text-db-yellow' },
  alert: { border: 'border-db-accent/60', chip: 'bg-db-accent/10 text-db-accent',   icon: 'text-db-accent' },
};

function AlertCard({ alert }: { alert: Alert }) {
  const { t } = useI18n();
  const Icon = CATEGORY_ICON[alert.category];
  const sev = SEVERITY_STYLES[alert.severity];
  return (
    <div className={`bg-db-card border ${sev.border} rounded-md p-3 flex flex-col gap-1.5`}>
      <div className="flex items-start gap-2">
        <Icon size={16} className={`shrink-0 mt-0.5 ${sev.icon}`} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-[10px] uppercase tracking-wide font-semibold px-1.5 py-0.5 rounded ${sev.chip}`}>
              {t('alertcat.' + alert.category)}
            </span>
            {alert.region && (
              <span className="text-[10px] text-db-muted flex items-center gap-1">
                <MapPin size={10} /> {alert.region}
              </span>
            )}
            <span className="text-[10px] text-db-muted">{t('alerts.since', { date: alert.valid_from })}</span>
          </div>
          <h4 className="text-sm font-semibold mt-1 leading-snug">{alert.title}</h4>
          <p className="text-xs text-db-muted mt-1 leading-relaxed">{alert.body}</p>
          {alert.action_label && (
            <div className="mt-1.5 text-[11px] text-db-accent font-medium">{alert.action_label} →</div>
          )}
        </div>
      </div>
    </div>
  );
}

export function OperationalAlerts() {
  const { t, lang } = useI18n();
  const { data, loading } = useApi<{ alerts: Alert[] }>(withLang('/api/customer/alerts', lang));
  const [showAll, setShowAll] = useState(false);

  if (loading || !data) return null;

  // Sort: alert > warn > info > good
  const order: Record<Alert['severity'], number> = { alert: 0, warn: 1, info: 2, good: 3 };
  const sorted = [...data.alerts].sort((a, b) => order[a.severity] - order[b.severity]);
  const visible = showAll ? sorted : sorted.slice(0, 3);

  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <div>
          <h3 className="text-sm font-semibold">{t('alerts.title')}</h3>
          <p className="text-xs text-db-muted">{t('alerts.subtitle', { n: data.alerts.length })}</p>
        </div>
        {sorted.length > 3 && (
          <button
            onClick={() => setShowAll((v) => !v)}
            className="text-xs text-db-muted hover:text-db-accent flex items-center gap-1 transition-colors"
          >
            {showAll ? <>{t('alerts.seeLess')} <ChevronUp size={12} /></> : <>{t('alerts.seeAll')} <ChevronDown size={12} /></>}
          </button>
        )}
      </div>
      <div className={`grid gap-2 ${showAll ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1 md:grid-cols-3'}`}>
        {visible.map((a) => (
          <AlertCard key={a.id} alert={a} />
        ))}
      </div>
    </div>
  );
}
