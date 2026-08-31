import { useState } from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Sparkles, Info } from 'lucide-react';
import { useT, tParts } from '../i18n';

interface DiscountStatus {
  status: string; // active | expiring_soon | expired | no_discount
  promo_name?: string | null;
  end_date?: string | null;
  days_to_expire?: number | null;
  last_discount_amt?: string | number | null;
  reason: string;
}

interface PaymentStatus {
  outstanding_balance: string | number;
  oldest_due_date?: string | null;
  days_overdue?: number | null;
  dunning_stage: number;
  next_action: string;
}

interface NextBestOffer {
  current_plan: string;
  current_fee: string | number;
  recommended_plan: string;
  recommended_fee: string | number;
  monthly_savings: string | number;
  rationale: string;
}

interface Props {
  discount: DiscountStatus | null;
  payment: PaymentStatus | null;
  nbo: NextBestOffer | null;
}

function fmt$(v: string | number | null | undefined): string {
  if (v === null || v === undefined) return '$0.00';
  const n = typeof v === 'string' ? parseFloat(v) : v;
  return `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

interface ChipBaseProps {
  tone: 'good' | 'warn' | 'alert' | 'neutral';
  icon: React.ReactNode;
  title: string;
  body: React.ReactNode;
  info?: { reasoning: string; suggestions: string[] };
}

function ChipBase({ tone, icon, title, body, info }: ChipBaseProps) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const styles = {
    good: 'border-db-green/40 bg-db-green/10 text-db-green',
    warn: 'border-db-yellow/40 bg-db-yellow/10 text-db-yellow',
    alert: 'border-db-accent/60 bg-db-accent/10 text-db-accent',
    neutral: 'border-db-border bg-db-card text-db-text',
  }[tone];
  return (
    <div className={`border rounded-md px-3 py-2 flex items-start gap-2 relative ${styles}`}>
      <div className="shrink-0 mt-0.5">{icon}</div>
      <div className="min-w-0 flex-1">
        <div className="text-xs font-semibold uppercase tracking-wide opacity-90 flex items-center gap-1.5">
          {title}
          {info && (
            <button
              type="button"
              onMouseEnter={() => setOpen(true)}
              onMouseLeave={() => setOpen(false)}
              onClick={() => setOpen((v) => !v)}
              className="opacity-70 hover:opacity-100 transition-opacity"
              aria-label={t('chip.howCalculated')}
            >
              <Info size={12} />
            </button>
          )}
        </div>
        <div className="text-sm text-db-text mt-0.5 leading-snug">{body}</div>
      </div>
      {info && open && (
        <div
          onMouseEnter={() => setOpen(true)}
          onMouseLeave={() => setOpen(false)}
          className="absolute z-20 top-full left-0 mt-1 w-80 bg-db-card border border-db-accent/40 rounded-md shadow-xl p-3 text-db-text"
        >
          <div className="text-xs font-semibold text-db-accent uppercase tracking-wide mb-1">{t('chip.calc')}</div>
          <div className="text-xs leading-relaxed text-db-muted mb-3">{info.reasoning}</div>
          <div className="text-xs font-semibold text-db-accent uppercase tracking-wide mb-1">{t('chip.howToOffer')}</div>
          <ul className="text-xs leading-relaxed text-db-text list-disc pl-4 space-y-0.5">
            {info.suggestions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function StatusChips({ discount, payment, nbo }: Props) {
  const t = useT();

  // Discount chip
  let discChip = null;
  if (discount) {
    if (discount.status === 'expired') {
      discChip = (
        <ChipBase
          tone="alert"
          icon={<AlertCircle size={16} />}
          title={t('chip.disc.expired.title')}
          body={tParts(t('chip.disc.expired.body'), {
            promo: <strong>{discount.promo_name}</strong>,
            date: <strong>{discount.end_date}</strong>,
            days: Math.abs(discount.days_to_expire || 0),
          })}
        />
      );
    } else if (discount.status === 'expiring_soon') {
      discChip = (
        <ChipBase
          tone="warn"
          icon={<AlertTriangle size={16} />}
          title={t('chip.disc.expiring.title')}
          body={tParts(t('chip.disc.expiring.body'), {
            promo: <strong>{discount.promo_name}</strong>,
            days: <strong>{discount.days_to_expire}</strong>,
          })}
        />
      );
    } else if (discount.status === 'active') {
      discChip = (
        <ChipBase
          tone="good"
          icon={<CheckCircle2 size={16} />}
          title={t('chip.disc.active.title')}
          body={tParts(t('chip.disc.active.body'), {
            promo: <strong>{discount.promo_name}</strong>,
            date: discount.end_date,
          })}
        />
      );
    } else if (discount.status === 'no_active_discount') {
      const daysAgo = Math.abs(discount.days_to_expire || 0);
      discChip = (
        <ChipBase
          tone="neutral"
          icon={<CheckCircle2 size={16} />}
          title={t('chip.disc.noActive.title')}
          body={tParts(t('chip.disc.noActive.body'), {
            promo: <strong>{discount.promo_name}</strong>,
            days: <strong>{daysAgo}</strong>,
          })}
        />
      );
    } else {
      discChip = (
        <ChipBase
          tone="neutral"
          icon={<CheckCircle2 size={16} />}
          title={t('chip.disc.none.title')}
          body={t('chip.disc.none.body')}
        />
      );
    }
  }

  // Payment chip — always show. If no record (no unpaid invoices), means al día.
  let payChip = (
    <ChipBase
      tone="good"
      icon={<CheckCircle2 size={16} />}
      title={t('chip.pay.current.title')}
      body={t('chip.pay.current.body')}
    />
  );
  if (payment) {
    const balance = parseFloat(String(payment.outstanding_balance));
    const stage = payment.dunning_stage;
    if (balance > 0 && stage >= 3) {
      payChip = (
        <ChipBase
          tone="alert"
          icon={<AlertCircle size={16} />}
          title={t('chip.pay.critical.title')}
          body={tParts(t('chip.pay.critical.body'), {
            balance: <strong>{fmt$(balance)}</strong>,
            days: payment.days_overdue,
            action: payment.next_action,
          })}
        />
      );
    } else if (balance > 0 && stage >= 1) {
      payChip = (
        <ChipBase
          tone="warn"
          icon={<AlertTriangle size={16} />}
          title={t('chip.pay.pending.title')}
          body={tParts(t('chip.pay.pending.body'), {
            balance: <strong>{fmt$(balance)}</strong>,
            days: payment.days_overdue,
            action: payment.next_action,
          })}
        />
      );
    }
  }

  // NBO chip
  let nboChip = null;
  if (nbo) {
    const savings = parseFloat(String(nbo.monthly_savings));

    // Language-independent scenario detection from structured fields.
    let scenario: 'overage' | 'underuse' | 'match' | 'fit';
    if (nbo.recommended_plan === nbo.current_plan) scenario = 'match';
    else if (savings < 0) scenario = 'overage'; // recommended costs more = upgrade for capacity
    else if (savings > 0) scenario = 'underuse'; // cheaper plan available
    else scenario = 'fit';

    const reasoning = t('chip.nbo.reasoning');

    const suggestionsMap: Record<typeof scenario, string[]> = {
      overage: [
        t('chip.nbo.overage.s0', { plan: nbo.recommended_plan }),
        t('chip.nbo.overage.s1'),
        t('chip.nbo.overage.s2'),
      ],
      underuse: [
        t('chip.nbo.underuse.s0'),
        t('chip.nbo.underuse.s1'),
        t('chip.nbo.underuse.s2'),
      ],
      match: [
        t('chip.nbo.match.s0'),
        t('chip.nbo.match.s1'),
        t('chip.nbo.match.s2'),
      ],
      fit: [
        t('chip.nbo.fit.s0', { plan: nbo.recommended_plan }),
        t('chip.nbo.fit.s1'),
      ],
    };

    if (scenario === 'overage') {
      nboChip = (
        <ChipBase
          tone="good"
          icon={<Sparkles size={16} />}
          title={t('chip.nbo.overage.title')}
          info={{ reasoning, suggestions: suggestionsMap.overage }}
          body={tParts(t('chip.nbo.overage.body'), { plan: <strong>{nbo.recommended_plan}</strong> })}
        />
      );
    } else if (scenario === 'underuse') {
      nboChip = (
        <ChipBase
          tone="neutral"
          icon={<Sparkles size={16} />}
          title={t('chip.nbo.underuse.title')}
          info={{ reasoning, suggestions: suggestionsMap.underuse }}
          body={tParts(t('chip.nbo.underuse.body'), { plan: <strong>{nbo.recommended_plan}</strong> })}
        />
      );
    } else if (scenario === 'match') {
      nboChip = (
        <ChipBase
          tone="neutral"
          icon={<Sparkles size={16} />}
          title={t('chip.nbo.match.title')}
          info={{ reasoning, suggestions: suggestionsMap.match }}
          body={t('chip.nbo.match.body')}
        />
      );
    } else {
      nboChip = (
        <ChipBase
          tone="neutral"
          icon={<Sparkles size={16} />}
          title={t('chip.nbo.fit.title')}
          info={{ reasoning, suggestions: suggestionsMap.fit }}
          body={tParts(t('chip.nbo.fit.body'), { plan: <strong>{nbo.recommended_plan}</strong> })}
        />
      );
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
      {discChip}
      {payChip}
      {nboChip}
    </div>
  );
}
