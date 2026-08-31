import { useEffect, useRef, useState } from 'react';
import { Search, X } from 'lucide-react';
import { useT } from '../i18n';

interface SearchResult {
  customer_id: string;
  full_name: string;
  segment: string;
  alert_count: number;
}

interface Props {
  onSelect: (id: string) => void;
  placeholder?: string;
  autoFocus?: boolean;
  variant?: 'large' | 'compact';
}

export function CustomerSearchBox({ onSelect, placeholder, autoFocus, variant = 'large' }: Props) {
  const t = useT();
  const [q, setQ] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [debounced, setDebounced] = useState('');
  const [loading, setLoading] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(q), 200);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    if (!debounced) {
      setResults([]);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetch(`/api/customer/list?search=${encodeURIComponent(debounced)}&limit=8`)
      .then((r) => r.json())
      .then((d) => {
        if (cancelled) return;
        setResults(d.rows || []);
        setLoading(false);
      })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [debounced]);

  // Click outside to close
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const pick = (id: string) => {
    onSelect(id);
    setQ('');
    setResults([]);
    setOpen(false);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && results[0]) pick(results[0].customer_id);
    if (e.key === 'Escape') setOpen(false);
  };

  const alertLabel = (count: number) =>
    count === 1 ? t('search.alert', { n: count }) : t('search.alerts', { n: count });

  const isLarge = variant === 'large';

  return (
    <div ref={wrapRef} className={`relative ${isLarge ? 'max-w-2xl mx-auto' : ''}`}>
      <Search size={isLarge ? 18 : 14} className={`absolute ${isLarge ? 'left-4 top-4' : 'left-3 top-2.5'} text-db-muted pointer-events-none`} />
      <input
        value={q}
        onChange={(e) => { setQ(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        autoFocus={autoFocus}
        placeholder={placeholder || t('search.placeholder')}
        className={`w-full bg-db-bg border border-db-border rounded-lg ${isLarge ? 'pl-12 pr-10 py-3 text-base' : 'pl-9 pr-9 py-2 text-sm'} placeholder:text-db-muted focus:outline-none focus:border-db-accent/50`}
      />
      {q && (
        <button
          onClick={() => { setQ(''); setResults([]); }}
          className={`absolute ${isLarge ? 'right-3 top-3.5' : 'right-2 top-2.5'} text-db-muted hover:text-db-text`}
          aria-label={t('search.clear')}
        >
          <X size={isLarge ? 16 : 14} />
        </button>
      )}
      {open && results.length > 0 && (
        <div className="absolute z-30 left-0 right-0 mt-1 bg-db-card border border-db-border rounded-md shadow-xl max-h-80 overflow-y-auto">
          {results.map((r) => (
            <button
              key={r.customer_id}
              onClick={() => pick(r.customer_id)}
              className="w-full text-left px-3 py-2.5 hover:bg-db-bg/60 border-b border-db-border/40 last:border-b-0 flex items-center justify-between gap-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-db-muted">{r.customer_id}</span>
                  <span className="text-[10px] text-db-muted uppercase">{r.segment}</span>
                </div>
                <div className="text-sm text-db-text truncate">{r.full_name}</div>
              </div>
              {r.alert_count > 0 && (
                <span className="text-[10px] uppercase tracking-wide bg-db-accent/15 text-db-accent px-1.5 py-0.5 rounded shrink-0">
                  {alertLabel(r.alert_count)}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
      {open && q && debounced && results.length === 0 && loading && (
        <div className="absolute z-30 left-0 right-0 mt-1 bg-db-card border border-db-border rounded-md p-4 text-center text-sm text-db-muted">
          {t('search.searching')}
        </div>
      )}
      {open && q && debounced && results.length === 0 && !loading && (
        <div className="absolute z-30 left-0 right-0 mt-1 bg-db-card border border-db-border rounded-md p-4 text-center text-sm text-db-muted">
          {t('search.noMatchesFor', { q })}
        </div>
      )}
    </div>
  );
}
