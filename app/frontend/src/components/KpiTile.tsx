import { TrendingUp, TrendingDown } from 'lucide-react';
import { useT } from '../i18n';

type Tone = 'neutral' | 'good' | 'warn' | 'alert';

export interface KpiTileData {
  id: string;
  label: string;
  value: number;
  format: 'currency' | 'percent' | 'count';
  trend?: number;
  subtitle?: string;
  tone?: Tone;
}

const toneStyles: Record<Tone, { ring: string; accent: string }> = {
  neutral: { ring: 'border-db-border',  accent: 'text-db-text' },
  good:    { ring: 'border-db-green/40', accent: 'text-db-green' },
  warn:    { ring: 'border-db-yellow/40', accent: 'text-db-yellow' },
  alert:   { ring: 'border-db-accent/60', accent: 'text-db-accent' },
};

function formatValue(v: number, fmt: KpiTileData['format']): string {
  if (fmt === 'currency') return `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (fmt === 'percent') return `${v.toFixed(1)}%`;
  return v.toLocaleString('en-US');
}

export function KpiTile({ tile }: { tile: KpiTileData }) {
  const tr = useT();
  const t = toneStyles[tile.tone || 'neutral'];
  const trendUp = (tile.trend ?? 0) > 0;
  const trendAbs = Math.abs(tile.trend ?? 0);
  return (
    <div className={`bg-db-card border ${t.ring} rounded-lg p-4 flex flex-col gap-2`}>
      <div className="text-xs text-db-muted uppercase tracking-wide">{tile.label}</div>
      <div className={`text-2xl font-semibold ${t.accent}`}>{formatValue(tile.value, tile.format)}</div>
      {tile.subtitle && <div className="text-xs text-db-muted">{tile.subtitle}</div>}
      {tile.trend !== undefined && trendAbs > 0.001 && (
        <div className={`flex items-center gap-1 text-xs ${trendUp ? 'text-db-green' : 'text-db-red'}`}>
          {trendUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          <span>
            {trendUp ? '+' : '−'}
            {tile.format === 'currency'
              ? `$${trendAbs.toFixed(2)}`
              : tile.format === 'percent'
              ? `${trendAbs.toFixed(1)}pp`
              : trendAbs.toFixed(0)} {tr('kpi.vsPrev')}
          </span>
        </div>
      )}
    </div>
  );
}
