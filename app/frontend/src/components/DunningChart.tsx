import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useT } from '../i18n';

interface Row {
  dunning_stage: number;
  pagos: number;
  clientes: number;
}

const COLORS = ['#22c55e', '#eab308', '#f97316', '#e60028', '#7f1018'];

export function DunningChart({ data }: { data: Row[] }) {
  const t = useT();
  const stageLabel = (stage: number) =>
    t('dunning.stage.' + stage) !== 'dunning.stage.' + stage
      ? t('dunning.stage.' + stage)
      : t('dunning.stagePrefix', { n: stage });
  const enriched = data.map((r) => {
    const stage = Math.round(r.dunning_stage);
    return {
      name: stageLabel(stage),
      value: r.pagos,
      clientes: r.clientes,
      stage,
    };
  });
  return (
    <div className="bg-db-card border border-db-border rounded-lg p-4">
      <h3 className="text-sm font-semibold mb-3">{t('dunning.title')}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={enriched}
            dataKey="value"
            nameKey="name"
            innerRadius={50}
            outerRadius={85}
            paddingAngle={2}
          >
            {enriched.map((e, i) => (
              <Cell key={i} fill={COLORS[e.stage] || '#444'} />
            ))}
          </Pie>
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
            formatter={(value: number, _: string, p: any) => [
              t('dunning.tooltip', { pagos: value, clientes: p.payload.clientes }),
              p.payload.name,
            ]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap gap-2 mt-3 text-xs">
        {enriched.map((e, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: COLORS[e.stage] || '#444' }} />
            <span className="text-db-muted">{e.name}: {e.clientes}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
