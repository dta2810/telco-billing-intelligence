import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { StatusChips } from './StatusChips';
import { InvoiceTrailChart, InvoiceTrailRow } from './InvoiceTrailChart';
import { InvoiceTrailTable } from './InvoiceTrailTable';
import { UsageTrailChart, UsageRow } from './UsageTrailChart';
import { UsageTrailTable } from './UsageTrailTable';
import { GenieChat } from './GenieChat';
import { PlanSimulator } from './PlanSimulator';
import { CustomerAvatar } from './CustomerAvatar';
import { Phone, Mail, Calendar, Layers, FileText } from 'lucide-react';
import { useI18n, withLang } from '../i18n';

interface ProfileResponse {
  header: {
    customer_id: string;
    full_name: string;
    segment: string;
    status: string;
    signup_date: string;
    email: string;
    msisdn_primary: string;
    active_subscriptions: number;
  };
  discount_status: any;
  payment_status: any;
  next_best_offer: any;
}

interface InvoicesResponse {
  trail: InvoiceTrailRow[];
  latest_lines: { charge_type: string; description: string; amount: string | number }[];
}

interface UsageResponse {
  trail: UsageRow[];
}

interface ContractResponse {
  contract: {
    contract_id: string;
    signed_date: string;
    end_date: string;
    term_months: number;
    early_termination_fee: string | number;
    auto_renew: boolean;
    days_remaining: number;
    status: string;
  } | null;
}

type Tab = 'summary' | 'actions' | 'chat';
const TABS: Tab[] = ['summary', 'actions', 'chat'];

export function CustomerDetailPanel({ customerId }: { customerId: string }) {
  const { t, lang } = useI18n();
  const profile = useApi<ProfileResponse>(withLang(`/api/customer/${customerId}/profile`, lang));
  const invoices = useApi<InvoicesResponse>(withLang(`/api/customer/${customerId}/invoices`, lang));
  const usage = useApi<UsageResponse>(withLang(`/api/customer/${customerId}/usage`, lang));
  const contract = useApi<ContractResponse>(withLang(`/api/customer/${customerId}/contract`, lang));
  const [tab, setTab] = useState<Tab>('summary');

  const chargeLabel = (ct: string) => {
    const key = 'detail.chargeType.' + ct;
    const label = t(key);
    return label === key ? ct : label;
  };

  const customerQuestions = [0, 1, 2, 3, 4, 5, 6].map((i) => t('detail.q.' + i));

  if (profile.loading) {
    return <div className="bg-db-card border border-db-border rounded-md p-6 text-db-muted text-sm">{t('common.loading')}</div>;
  }
  if (profile.error || !profile.data) {
    return <div className="bg-db-card border border-db-border rounded-md p-6 text-db-red text-sm">{t('common.error')}: {profile.error}</div>;
  }

  const h = profile.data.header;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="bg-db-card border border-db-border rounded-md p-4">
        <div className="flex items-start gap-4">
          <CustomerAvatar name={h.full_name} id={h.customer_id} size={56} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-semibold">{h.full_name}</h2>
              <span className="text-xs px-1.5 py-0.5 rounded bg-db-border/50 text-db-muted uppercase">{h.segment}</span>
            </div>
            <div className="font-mono text-xs text-db-muted">{h.customer_id}</div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-db-muted">
              <span className="flex items-center gap-1"><Phone size={11} /> {h.msisdn_primary}</span>
              <span className="flex items-center gap-1"><Mail size={11} /> {h.email}</span>
              <span className="flex items-center gap-1"><Calendar size={11} /> {t('detail.signup', { date: h.signup_date })}</span>
              <span className="flex items-center gap-1"><Layers size={11} /> {t('detail.activeLines', { n: h.active_subscriptions })}</span>
            </div>
          </div>
        </div>

        {/* Status chips */}
        <div className="mt-4">
          <StatusChips
            discount={profile.data.discount_status}
            payment={profile.data.payment_status}
            nbo={profile.data.next_best_offer}
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-db-card border border-db-border rounded-md overflow-hidden">
        <div className="flex border-b border-db-border">
          {TABS.map((tb) => (
            <button
              key={tb}
              onClick={() => setTab(tb)}
              className={`px-4 py-2.5 text-sm transition-colors ${
                tab === tb
                  ? 'text-db-accent border-b-2 border-db-accent'
                  : 'text-db-muted hover:text-db-text'
              }`}
            >
              {t('detail.tab.' + tb)}
            </button>
          ))}
        </div>

        <div className="p-4">
          {tab === 'summary' && (
            <div className="space-y-4">
              {invoices.data ? (
                <>
                  {/* Sección 1: Evolución de la factura — chart izq + tabla der */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <InvoiceTrailChart data={invoices.data.trail} />
                    <InvoiceTrailTable data={invoices.data.trail} />
                  </div>

                  {/* Sección 2: Evolución de consumo — chart izq + tabla der */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {usage.data ? (
                      <>
                        <UsageTrailChart
                          data={usage.data.trail}
                          invoiceTotalByPeriod={Object.fromEntries(
                            invoices.data.trail.map((r) => [
                              r.billing_period,
                              parseFloat(String(r.total_due)),
                            ])
                          )}
                        />
                        <UsageTrailTable data={usage.data.trail} />
                      </>
                    ) : (
                      <div className="bg-db-card border border-db-border rounded-md p-4 text-db-muted text-sm lg:col-span-2">
                        {t('detail.loadingUsage')}
                      </div>
                    )}
                  </div>

                  {/* Detalle itemizado de la última factura (descripciones humanas) */}
                  <div className="bg-db-card border border-db-border rounded-md p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <FileText size={16} className="text-db-accent" />
                      <h4 className="text-sm font-semibold">{t('detail.lastInvoice')}</h4>
                      {invoices.data.trail.length > 0 && (
                        <span className="text-xs text-db-muted">
                          {t('detail.invoiceMeta', {
                            period: invoices.data.trail[invoices.data.trail.length - 1].billing_period,
                            amt: '$' + parseFloat(String(invoices.data.trail[invoices.data.trail.length - 1].total_due)).toFixed(2),
                          })}
                        </span>
                      )}
                    </div>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-db-muted text-xs uppercase tracking-wide border-b border-db-border">
                          <th className="text-left py-2 pr-3">{t('detail.col.concept')}</th>
                          <th className="text-left py-2 pr-3">{t('detail.col.description')}</th>
                          <th className="text-right py-2">{t('detail.col.amount')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {invoices.data.latest_lines.map((l, i) => {
                          const amt = parseFloat(String(l.amount));
                          const label = chargeLabel(l.charge_type);
                          return (
                            <tr key={i} className="border-b border-db-border/40">
                              <td className="py-2 pr-3">
                                <span className="text-xs px-2 py-0.5 rounded bg-db-border/50 text-db-text">{label}</span>
                              </td>
                              <td className="py-2 pr-3 text-db-text">{l.description}</td>
                              <td className={`py-2 text-right tabular-nums ${amt < 0 ? 'text-db-green' : 'text-db-text'}`}>
                                {amt < 0 ? '−' : ''}${Math.abs(amt).toFixed(2)}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="text-db-muted text-sm">{t('detail.loadingInvoices')}</div>
              )}
            </div>
          )}

          {tab === 'actions' && (
            <div className="space-y-4">
              {contract.data?.contract && (
                <div className="bg-db-bg border border-db-border rounded-md p-3 text-sm">
                  <div className="text-xs text-db-muted uppercase tracking-wide mb-1">{t('detail.activeContract')}</div>
                  <div>
                    {t('detail.contractEnds')} <strong>{contract.data.contract.end_date}</strong>{' '}
                    <span className="text-db-muted">
                      ({t('detail.daysRemaining', { n: contract.data.contract.days_remaining })})
                    </span>
                    , ETF <strong>${parseFloat(String(contract.data.contract.early_termination_fee)).toFixed(2)}</strong>
                    {contract.data.contract.auto_renew ? t('detail.autoRenew') : ''}
                  </div>
                </div>
              )}
              <PlanSimulator customerId={customerId} />
            </div>
          )}

          {tab === 'chat' && (
            <GenieChat
              context={t('detail.chatContext', { id: h.customer_id })}
              suggestedQuestions={customerQuestions}
              customerId={h.customer_id}
              height={500}
              useMemory
            />
          )}
        </div>
      </div>
    </div>
  );
}
