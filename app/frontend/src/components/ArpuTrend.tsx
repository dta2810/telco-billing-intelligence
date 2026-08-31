import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useT } from '../i18n';

interface Point {
  billing_period: string;
  arpu: number;
  revenue: number;
}

export function ArpuTrend({ data }: { data: Point[] }) {
  const t = useT();
  return (
    <div className="bg-db-card border border-db-border rounded-lg p-4">
      <h3 className="text-sm font-semibold mb-3">{t('arpu.title')}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis dataKey="billing_period" stroke="#a1a1a1" fontSize={11} />
          <YAxis
            stroke="#a1a1a1"
            fontSize={11}
            tickFormatter={(v) => `$${v.toFixed(2)}`}
            domain={[(dataMin: number) => Math.floor(dataMin - 1), (dataMax: number) => Math.ceil(dataMax + 1)]}
          />
          <Tooltip
            contentStyle={{
              background: '#161616',
              border: '1px solid #e60028',
              borderRadius: 6,
              padding: '8px 12px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
            }}
            labelStyle={{ color: '#f5f5f5', fontWeight: 600, marginBottom: 4 }}
            itemStyle={{ color: '#f5f5f5', fontSize: 13 }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, 'ARPU']}
            cursor={{ stroke: '#e60028', strokeOpacity: 0.3, strokeWidth: 1 }}
          />
          <Line
            type="monotone"
            dataKey="arpu"
            stroke="#e60028"
            strokeWidth={3}
            dot={{ r: 5, fill: '#e60028', stroke: '#fff', strokeWidth: 1 }}
            activeDot={{ r: 7 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
