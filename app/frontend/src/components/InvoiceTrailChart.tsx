import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, ReferenceLine,
} from 'recharts';
import { useT } from '../i18n';

export interface InvoiceTrailRow {
  billing_period: string;
  total_due: string | number;
  recurring: string | number | null;
  discount: string | number | null;
  overage: string | number | null;
  device_subsidy: string | number | null;
  status: string;
}

function n(v: any): number { return v == null ? 0 : parseFloat(String(v)); }

export function InvoiceTrailChart({ data }: { data: InvoiceTrailRow[] }) {
  const t = useT();
  const cleaned = data.map((r) => ({
    period: r.billing_period,
    plan:     n(r.recurring),
    device:   n(r.device_subsidy),
    overage:  n(r.overage),
    discount: -Math.abs(n(r.discount)),
    total: n(r.total_due),
  }));
  return (
    <div className="bg-db-card border border-db-border rounded-md p-4 h-full">
      <h4 className="text-sm font-semibold mb-3">{t('invoice.title')}</h4>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={cleaned} stackOffset="sign">
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis dataKey="period" stroke="#a1a1a1" fontSize={11} />
          <YAxis stroke="#a1a1a1" fontSize={11} tickFormatter={(v) => `$${v.toFixed(0)}`} />
          <Tooltip
            contentStyle={{
              background: '#161616',
              border: '1px solid #2a2a2a',
              borderRadius: 6,
              padding: '6px 10px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
            }}
            labelStyle={{ color: '#f5f5f5', fontWeight: 600, fontSize: 12, marginBottom: 2 }}
            itemStyle={{ display: 'none' }}
            cursor={{ fill: 'rgba(230,0,40,0.05)' }}
            formatter={() => ['', '']}
            content={({ active, payload, label }) => {
              if (!active || !payload || !payload.length) return null;
              const row = payload[0].payload as { total: number };
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
                    {t('invoice.total', { total: `$${row.total.toFixed(2)}` })}
                  </div>
                </div>
              );
            }}
          />
          <ReferenceLine y={0} stroke="#444" />
          <Legend wrapperStyle={{ fontSize: 11, color: '#a1a1a1' }} />
          <Bar dataKey="plan"     name={t('invoice.plan')}     stackId="a" fill="#3b82f6" />
          <Bar dataKey="device"   name={t('invoice.device')}   stackId="a" fill="#8b5cf6" />
          <Bar dataKey="overage"  name={t('invoice.overage')}  stackId="a" fill="#f97316" />
          <Bar dataKey="discount" name={t('invoice.discount')} stackId="a" fill="#22c55e" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
