import { UsageRow } from './UsageTrailChart';
import { useT } from '../i18n';

function n(v: any): number { return v == null ? 0 : parseFloat(String(v)); }

export function UsageTrailTable({ data }: { data: UsageRow[] }) {
  const t = useT();
  const lastIdx = data.length - 1;
  return (
    <div className="bg-db-card border border-db-border rounded-md p-4 h-full">
      <h4 className="text-sm font-semibold mb-3">{t('table.byMonth')}</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-xs tabular-nums">
          <thead>
            <tr className="text-db-muted uppercase tracking-wide border-b border-db-border">
              <th className="text-left py-2 pr-2 font-medium">{t('table.month')}</th>
              <th className="text-right py-2 px-2 font-medium">{t('usgtbl.data')}</th>
              <th className="text-right py-2 px-2 font-medium">{t('usgtbl.overage')}</th>
              <th className="text-right py-2 px-2 font-medium">{t('usgtbl.roaming')}</th>
              <th className="text-right py-2 px-2 font-medium">{t('usgtbl.voice')}</th>
              <th className="text-right py-2 pl-2 font-medium">{t('usgtbl.sms')}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r, i) => {
              const isLast = i === lastIdx;
              const dataGb = n(r.data_gb);
              const overGb = n(r.overage_gb);
              const roamGb = +(n(r.roaming_mb) / 1024).toFixed(2);
              const voz = n(r.voice_min);
              const sms = n(r.sms);
              return (
                <tr
                  key={r.billing_period}
                  className={`border-b border-db-border/40 ${
                    isLast ? 'bg-db-accent/10 border-l-2 border-l-db-accent' : ''
                  }`}
                >
                  <td className={`py-2 pr-2 ${isLast ? 'font-semibold text-db-text pl-2' : 'text-db-muted'}`}>
                    {r.billing_period}
                  </td>
                  <td className="py-2 px-2 text-right text-db-text">{dataGb.toFixed(1)} GB</td>
                  <td className={`py-2 px-2 text-right ${overGb > 0 ? 'text-db-orange' : 'text-db-text'}`}>
                    {overGb > 0 ? `${overGb.toFixed(2)} GB` : '—'}
                  </td>
                  <td className="py-2 px-2 text-right text-db-text">
                    {roamGb > 0 ? `${roamGb.toFixed(2)} GB` : '—'}
                  </td>
                  <td className="py-2 px-2 text-right text-db-text">{voz.toLocaleString()} {t('sim.min')}</td>
                  <td className={`py-2 pl-2 text-right ${isLast ? 'font-semibold text-db-text' : 'text-db-text'}`}>
                    {sms.toLocaleString()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
