import { useEffect, useMemo, useState } from 'react';
import { Users, Filter } from 'lucide-react';
import { GenieChat } from './GenieChat';
import { CustomerRow, ListResponse } from './CustomerListPanel';
import { useT } from '../i18n';

const FILTER_KEYS = ['mora_60', 'expired_discount', 'contract_expiring', 'overage'];
const SEGMENTS = ['todos', 'consumer', 'smb', 'enterprise'];

export function CohortExplorer() {
  const t = useT();
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [segment, setSegment] = useState<string>('todos');
  const [list, setList] = useState<ListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const presetFallback = useMemo(
    () => [0, 1, 2, 3, 4, 5].map((i) => t('cohort.fallback.' + i)),
    [t]
  );

  useEffect(() => {
    if (!activeFilter && segment === 'todos') {
      setList(null);
      setError(false);
      return;
    }
    const params = new URLSearchParams();
    if (activeFilter) params.set(activeFilter, 'true');
    if (segment !== 'todos') params.set('segment', segment);
    params.set('limit', '50');
    // cancel stale requests; surface backend errors instead of crashing
    const ctrl = new AbortController();
    setLoading(true);
    setError(false);
    fetch(`/api/customer/list?${params.toString()}`, { signal: ctrl.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: ListResponse) => setList({ count: d.count ?? 0, rows: d.rows ?? [] }))
      .catch((e) => {
        if (ctrl.signal.aborted) return;
        console.error('customer/list failed', e);
        setList(null);
        setError(true);
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false);
      });
    return () => ctrl.abort();
  }, [activeFilter, segment]);

  const presetQuestions = useMemo(() => {
    if (activeFilter) {
      const ctx = t('cohort.preset.' + activeFilter);
      return [ctx, ...presetFallback.slice(0, 5)];
    }
    return presetFallback;
  }, [activeFilter, presetFallback, t]);

  const contextLabel = activeFilter
    ? t('cohort.contextCohort', { label: t('filter.' + activeFilter) }) +
      (segment !== 'todos' ? ` · ${t('segment.' + segment)}` : '')
    : t('cohort.contextPortfolio');

  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between">
        <div>
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Filter size={16} className="text-db-accent" /> {t('cohort.title')}
          </h3>
          <p className="text-xs text-db-muted mt-0.5">{t('cohort.subtitle')}</p>
        </div>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2 items-center">
        {FILTER_KEYS.map((key) => {
          const active = activeFilter === key;
          return (
            <button
              key={key}
              onClick={() => setActiveFilter(active ? null : key)}
              className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
                active
                  ? 'bg-db-accent/15 text-db-accent border-db-accent/40'
                  : 'bg-db-card text-db-muted border-db-border hover:text-db-text'
              }`}
            >
              {t('filter.' + key)}
            </button>
          );
        })}
        <span className="text-db-muted text-xs ml-2">|</span>
        <div className="flex gap-1 text-xs">
          {SEGMENTS.map((s) => (
            <button
              key={s}
              onClick={() => setSegment(s)}
              className={`px-2 py-1 rounded-md transition-colors ${
                segment === s
                  ? 'bg-db-border/50 text-db-text'
                  : 'text-db-muted hover:text-db-text'
              }`}
            >
              {t('segment.' + s)}
            </button>
          ))}
        </div>
      </div>

      {/* Two-column: list + chat */}
      <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-4">
        <div className="bg-db-card border border-db-border rounded-md flex flex-col h-[540px] overflow-hidden">
          <div className="px-3 py-2 border-b border-db-border flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-db-muted">
              <Users size={12} /> {t('cohort.inCohort')}
            </span>
            <span className="text-db-muted">{list ? `${list.count}` : '—'}</span>
          </div>
          <div className="flex-1 overflow-y-auto">
            {!activeFilter && segment === 'todos' && (
              <div className="text-center py-10 px-4 text-sm text-db-muted">
                {t('cohort.activateFilter')}
              </div>
            )}
            {loading && (
              <div className="text-center py-10 text-db-muted text-sm">{t('common.loading')}</div>
            )}
            {error && !loading && (
              <div className="text-center py-10 text-db-muted text-sm">{t('common.loadFailed')}</div>
            )}
            {list?.rows?.map((c: CustomerRow) => (
              <a
                key={c.customer_id}
                href={`/customer?selected=${c.customer_id}`}
                className="block w-full text-left px-3 py-2 border-b border-db-border/60 hover:bg-db-bg/40 transition-colors"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-db-muted">{c.customer_id}</span>
                  {c.alert_count > 0 && (
                    <span className="text-[10px] uppercase tracking-wide bg-db-accent/15 text-db-accent px-1.5 py-0.5 rounded">
                      {c.alert_count}
                    </span>
                  )}
                </div>
                <div className="text-sm text-db-text truncate">{c.full_name}</div>
                <div className="text-[11px] text-db-muted capitalize">{c.segment}</div>
              </a>
            ))}
            {list?.rows?.length === 0 && !loading && (
              <div className="text-center py-10 text-db-muted text-sm">{t('common.noMatches')}</div>
            )}
          </div>
        </div>

        <GenieChat
          context={contextLabel}
          suggestedQuestions={presetQuestions}
          height={540}
        />
      </div>
    </div>
  );
}
