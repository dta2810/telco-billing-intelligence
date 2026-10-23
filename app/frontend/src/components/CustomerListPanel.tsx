import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import { useT } from '../i18n';

export interface CustomerRow {
  customer_id: string;
  full_name: string;
  segment: string;
  status: string;
  signup_date: string;
  f_mora_60: boolean;
  f_mora_30: boolean;
  f_expired_discount: boolean;
  f_contract_expiring: boolean;
  f_overage: boolean;
  alert_count: number;
}

export interface ListResponse {
  count: number;
  rows: CustomerRow[];
}

const FILTER_KEYS = ['mora_60', 'expired_discount', 'contract_expiring', 'overage'];
const SEGMENTS = ['todos', 'consumer', 'smb', 'enterprise'];

interface Props {
  onSelect: (id: string) => void;
  selectedId: string | null;
  filters: Set<string>;
  onToggleFilter: (key: string) => void;
  segment: string;
  onSegmentChange: (s: string) => void;
  searchValue: string;
  onSearchChange: (s: string) => void;
  renderList: boolean;
}

export function CustomerListPanel({
  onSelect,
  selectedId,
  filters,
  onToggleFilter,
  segment,
  onSegmentChange,
  searchValue,
  onSearchChange,
  renderList,
}: Props) {
  const t = useT();
  const [data, setData] = useState<ListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [debounced, setDebounced] = useState(searchValue);

  useEffect(() => {
    const tm = setTimeout(() => setDebounced(searchValue), 250);
    return () => clearTimeout(tm);
  }, [searchValue]);

  useEffect(() => {
    if (!renderList) {
      setData(null);
      setError(false);
      return;
    }
    const params = new URLSearchParams();
    filters.forEach((f) => params.set(f, 'true'));
    if (segment !== 'todos') params.set('segment', segment);
    if (debounced) params.set('search', debounced);
    // cancel stale requests; surface backend errors instead of crashing
    const ctrl = new AbortController();
    setLoading(true);
    setError(false);
    fetch(`/api/customer/list?${params.toString()}`, { signal: ctrl.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: ListResponse) => setData({ count: d.count ?? 0, rows: d.rows ?? [] }))
      .catch((e) => {
        if (ctrl.signal.aborted) return;
        console.error('customer/list failed', e);
        setData(null);
        setError(true);
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false);
      });
    return () => ctrl.abort();
  }, [filters, segment, debounced, renderList]);

  const alertLabel = (count: number) =>
    count === 1 ? t('search.alert', { n: count }) : t('search.alerts', { n: count });

  const FlagDot = ({ active, color }: { active: boolean; color: string }) =>
    active ? <span className={`w-1.5 h-1.5 rounded-full ${color}`} /> : null;

  return (
    <div className="bg-db-card border border-db-border rounded-md flex flex-col h-full overflow-hidden">
      {/* Filters */}
      <div className="p-3 border-b border-db-border space-y-3 shrink-0">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-2.5 text-db-muted" />
          <input
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={t('list.placeholder')}
            autoFocus
            className="w-full pl-9 pr-3 py-2 bg-db-bg border border-db-border rounded-md text-sm placeholder:text-db-muted focus:outline-none focus:border-db-accent/50"
          />
        </div>
        <div className="flex flex-wrap gap-1">
          {FILTER_KEYS.map((key) => {
            const active = filters.has(key);
            return (
              <button
                key={key}
                onClick={() => onToggleFilter(key)}
                className={`px-2 py-1 rounded-full text-xs border transition-colors ${
                  active
                    ? 'bg-db-accent/15 text-db-accent border-db-accent/40'
                    : 'bg-db-bg text-db-muted border-db-border hover:text-db-text'
                }`}
              >
                {t('filter.' + key)}
              </button>
            );
          })}
        </div>
        <div className="flex gap-1 text-xs">
          {SEGMENTS.map((s) => (
            <button
              key={s}
              onClick={() => onSegmentChange(s)}
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
        {renderList && (
          <div className="text-xs text-db-muted">
            {loading ? t('common.loading') : data ? t('list.count', { n: data.count }) : '—'}
          </div>
        )}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {!renderList && (
          <div className="text-center py-10 px-6">
            <Search size={28} className="mx-auto text-db-accent/30 mb-3" />
            <p className="text-sm text-db-muted leading-relaxed">{t('list.emptyHint')}</p>
          </div>
        )}
        {renderList && error && !loading && (
          <div className="text-center py-10 text-db-muted text-sm">{t('common.loadFailed')}</div>
        )}
        {renderList && data?.rows?.map((c) => {
          const active = c.customer_id === selectedId;
          return (
            <button
              key={c.customer_id}
              onClick={() => onSelect(c.customer_id)}
              className={`w-full text-left px-3 py-2.5 border-b border-db-border/60 transition-colors ${
                active ? 'bg-db-accent/10 border-l-2 border-l-db-accent' : 'hover:bg-db-bg/40'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-db-muted">{c.customer_id}</span>
                {c.alert_count > 0 && (
                  <span className="text-[10px] uppercase tracking-wide bg-db-accent/15 text-db-accent px-1.5 py-0.5 rounded">
                    {alertLabel(c.alert_count)}
                  </span>
                )}
              </div>
              <div className="text-sm text-db-text truncate mt-0.5">{c.full_name}</div>
              <div className="flex items-center gap-2 mt-1.5 text-[11px] text-db-muted">
                <span className="capitalize">{c.segment}</span>
                <span>·</span>
                <div className="flex items-center gap-1">
                  <FlagDot active={c.f_mora_60} color="bg-db-accent" />
                  <FlagDot active={c.f_mora_30} color="bg-db-yellow" />
                  <FlagDot active={c.f_expired_discount} color="bg-db-orange" />
                  <FlagDot active={c.f_contract_expiring} color="bg-purple-500" />
                  <FlagDot active={c.f_overage} color="bg-blue-400" />
                </div>
              </div>
            </button>
          );
        })}
        {renderList && data?.rows?.length === 0 && !loading && (
          <div className="text-center py-10 text-db-muted text-sm">{t('list.noMatch')}</div>
        )}
      </div>
    </div>
  );
}
