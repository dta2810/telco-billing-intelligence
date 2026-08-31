import {
  ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { useT } from '../i18n';

export interface UsageRow {
  billing_period: string;
  voice_min: number | string;
  data_mb: number | string;
  data_gb: number | string;
  sms: number | string;
  overage_mb: number | string;
  overage_gb: number | string;
  roaming_mb: number | string;
}

function n(v: any): number { return v == null ? 0 : parseFloat(String(v)); }

interface UsageTrailChartProps {
  data: UsageRow[];
  invoiceTotalByPeriod?: Record<string, number>;
}

export function UsageTrailChart({ data, invoiceTotalByPeriod }: UsageTrailChartProps) {
  const t = useT();
  const cleaned = data.map((r) => ({
    period: r.billing_period,
    data:    n(r.data_gb),
    overage: n(r.overage_gb),
    roaming: +(n(r.roaming_mb) / 1024).toFixed(2),
    voice:   n(r.voice_min),
    sms:     n(r.sms),
  }));
  return (
    <div className="bg-db-card border border-db-border rounded-md p-4 h-full">
      <h4 className="text-sm font-semibold mb-3">{t('usage.title')}</h4>
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={cleaned}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis dataKey="period" stroke="#a1a1a1" fontSize={11} />
          <YAxis
            yAxisId="gb"
            orientation="left"
            stroke="#3b82f6"
            fontSize={11}
            tickFormatter={(v) => `${v} GB`}
          />
          <YAxis
            yAxisId="cnt"
            orientation="right"
            stroke="#a1a1a1"
            fontSize={11}
          />
          <Tooltip
            cursor={{ fill: 'rgba(230,0,40,0.05)' }}
            content={({ active, payload, label }) => {
              if (!active || !payload || !payload.length) return null;
              const total = invoiceTotalByPeriod?.[label as string];
              return (
                <div style={{
                  background: '#161616',
                  border: '1px solid #2a2a2a',
                  borderRadius: 6,
                  padding: '6px 10px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
                }}>
                  <div style={{ color: '#f5f5f5', fontWeight: 600, fontSize: 12 }}>{label}</div>
                  <div style={{ color: '#f5f5f5', fontSize: 13 }}>
                    {total != null ? t('usage.totalInvoice', { total: `$${total.toFixed(2)}` }) : t('usage.noInvoice')}
                  </div>
                </div>
              );
            }}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: '#a1a1a1' }} />
          <Bar yAxisId="gb" dataKey="data" name={t('usage.data')} fill="#3b82f6" />
          <Bar yAxisId="gb" dataKey="overage" name={t('usage.overage')} fill="#f97316" />
          <Bar yAxisId="gb" dataKey="roaming" name={t('usage.roaming')} fill="#8b5cf6" />
          <Line yAxisId="cnt" type="monotone" dataKey="voice" name={t('usage.voice')} stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
          <Line yAxisId="cnt" type="monotone" dataKey="sms" name={t('usage.sms')} stroke="#eab308" strokeWidth={2} dot={{ r: 3 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
