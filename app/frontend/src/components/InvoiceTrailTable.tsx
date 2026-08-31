import { InvoiceTrailRow } from './InvoiceTrailChart';
import { useT } from '../i18n';

function n(v: any): number { return v == null ? 0 : parseFloat(String(v)); }
function fmt(v: number): string {
  if (v === 0) return '—';
  return `$${v.toFixed(2)}`;
}

export function InvoiceTrailTable({ data }: { data: InvoiceTrailRow[] }) {
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
              <th className="text-right py-2 px-2 font-medium">{t('invtbl.plan')}</th>
              <th className="text-right py-2 px-2 font-medium">{t('invtbl.device')}</th>
              <th className="text-right py-2 px-2 font-medium">{t('invtbl.overage')}</th>
              <th className="text-right py-2 px-2 font-medium">{t('invtbl.discount')}</th>
              <th className="text-right py-2 pl-2 font-medium">{t('invtbl.total')}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r, i) => {
              const isLast = i === lastIdx;
              const discount = -Math.abs(n(r.discount));
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
                  <td className="py-2 px-2 text-right text-db-text">{fmt(n(r.recurring))}</td>
                  <td className="py-2 px-2 text-right text-db-text">{fmt(n(r.device_subsidy))}</td>
                  <td className={`py-2 px-2 text-right ${n(r.overage) > 0 ? 'text-db-orange' : 'text-db-text'}`}>
                    {fmt(n(r.overage))}
                  </td>
                  <td className={`py-2 px-2 text-right ${discount < 0 ? 'text-db-green' : 'text-db-text'}`}>
                    {discount < 0 ? `−$${Math.abs(discount).toFixed(2)}` : '—'}
                  </td>
                  <td className={`py-2 pl-2 text-right ${isLast ? 'font-semibold text-db-text' : 'text-db-text'}`}>
                    ${n(r.total_due).toFixed(2)}
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
