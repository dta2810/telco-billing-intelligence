import { useEffect, useState } from 'react';
import { ArrowRightLeft, AlertTriangle } from 'lucide-react';
import { useI18n, withLang } from '../i18n';

interface Plan {
  plan_id: string;
  plan_name: string;
  monthly_fee: string | number;
  data_quota_gb: number;
  voice_minutes: number;
}

interface SimResult {
  current_plan: string;
  current_fee: string | number;
  current_data_gb: number;
  current_voice_min: number;
  current_sms: number;
  new_plan: string;
  new_fee: string | number;
  new_data_gb: number;
  new_voice_min: number;
  new_sms: number;
  monthly_delta: string | number;
  annual_delta: string | number;
  data_delta_gb: number;
  voice_delta_min: number;
  warning: string;
}

function fmt$(v: any): string {
  const n = typeof v === 'string' ? parseFloat(v) : v;
  return `$${(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtData(gb: number): string {
  return `${gb} GB`;
}

export function PlanSimulator({ customerId }: { customerId: string }) {
  const { t, lang } = useI18n();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [result, setResult] = useState<SimResult | null>(null);
  const [loading, setLoading] = useState(false);

  const fmtVoice = (v: number): string => {
    if (v === -1 || v === null || v === undefined) return t('sim.unlimited');
    return `${v.toLocaleString('en-US')} ${t('sim.min')}`;
  };

  useEffect(() => {
    fetch('/api/plans')
      .then((r) => r.json())
      .then((d) => setPlans(d.plans || []));
  }, []);

  const simulate = async () => {
    if (!selected) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(withLang(`/api/customer/${customerId}/action/simulate_plan_change`, lang), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_plan_id: selected }),
      });
      const d = await res.json();
      setResult(d.result);
    } finally {
      setLoading(false);
    }
  };

  const PlanCard = ({ title, label, fee, dataGb, voiceMin, sms }: {
    title: string; label: string;
    fee: string | number; dataGb: number; voiceMin: number; sms: number;
  }) => (
    <div className="bg-db-bg border border-db-border rounded-md p-3">
      <div className="text-xs text-db-muted uppercase tracking-wide">{title}</div>
      <div className="text-sm mt-1 font-medium">{label}</div>
      <div className="text-base font-semibold text-db-text mt-1">{fmt$(fee)}{t('sim.perMonth')}</div>
      <dl className="mt-2 space-y-1 text-xs">
        <div className="flex justify-between">
          <dt className="text-db-muted">{t('sim.data')}</dt>
          <dd>{fmtData(dataGb)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-db-muted">{t('sim.voice')}</dt>
          <dd>{fmtVoice(voiceMin)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-db-muted">{t('sim.sms')}</dt>
          <dd>{sms === -1 ? t('sim.unlimited') : sms.toLocaleString('en-US')}</dd>
        </div>
      </dl>
    </div>
  );

  const monthly = result ? parseFloat(String(result.monthly_delta)) : 0;
  const annual = result ? parseFloat(String(result.annual_delta)) : 0;

  return (
    <div className="bg-db-card border border-db-border rounded-md p-4">
      <div className="flex items-center gap-2 mb-3">
        <ArrowRightLeft size={16} className="text-db-accent" />
        <h4 className="text-sm font-semibold">{t('sim.title')}</h4>
      </div>
      <div className="flex gap-2 items-center">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="flex-1 bg-db-bg border border-db-border rounded-md px-3 py-2 text-sm"
        >
          <option value="">{t('sim.selectPlan')}</option>
          {plans.map((p) => (
            <option key={p.plan_id} value={p.plan_id}>
              {p.plan_name} — {fmt$(p.monthly_fee)}{t('sim.perMonth')} · {p.data_quota_gb}GB
            </option>
          ))}
        </select>
        <button
          onClick={simulate}
          disabled={!selected || loading}
          className="bg-db-accent hover:bg-accent-soft disabled:opacity-50 text-white px-4 py-2 rounded-md text-sm transition-colors"
        >
          {loading ? '…' : t('sim.simulate')}
        </button>
      </div>

      {result && (
        <div className="mt-4 space-y-3">
          {/* Plan comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <PlanCard
              title={t('sim.currentPlan')}
              label={result.current_plan}
              fee={result.current_fee}
              dataGb={result.current_data_gb}
              voiceMin={result.current_voice_min}
              sms={result.current_sms}
            />
            <PlanCard
              title={t('sim.proposedPlan')}
              label={result.new_plan}
              fee={result.new_fee}
              dataGb={result.new_data_gb}
              voiceMin={result.new_voice_min}
              sms={result.new_sms}
            />
          </div>

          {/* Impact summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div
              className={`rounded-md p-3 border ${
                monthly < 0
                  ? 'border-db-green/40 bg-db-green/10'
                  : monthly > 0
                  ? 'border-db-yellow/40 bg-db-yellow/10'
                  : 'border-db-border bg-db-bg'
              }`}
            >
              <div className="text-xs uppercase tracking-wide opacity-90">{t('sim.cost')}</div>
              <div className={`text-base font-semibold mt-1 ${monthly < 0 ? 'text-db-green' : monthly > 0 ? 'text-db-yellow' : ''}`}>
                {monthly < 0 ? '−' : monthly > 0 ? '+' : ''}
                {fmt$(Math.abs(monthly))}{t('sim.perMonth')}
              </div>
              <div className="text-xs text-db-muted">
                {annual === 0
                  ? t('sim.noChange')
                  : annual < 0
                  ? t('sim.annualSaving', { v: fmt$(Math.abs(annual)) })
                  : t('sim.annualExtra', { v: fmt$(Math.abs(annual)) })}
              </div>
            </div>
            <div
              className={`rounded-md p-3 border ${
                result.data_delta_gb > 0
                  ? 'border-db-green/40 bg-db-green/10'
                  : result.data_delta_gb < 0
                  ? 'border-db-yellow/40 bg-db-yellow/10'
                  : 'border-db-border bg-db-bg'
              }`}
            >
              <div className="text-xs uppercase tracking-wide opacity-90">{t('sim.data')}</div>
              <div className={`text-base font-semibold mt-1 ${result.data_delta_gb > 0 ? 'text-db-green' : result.data_delta_gb < 0 ? 'text-db-yellow' : ''}`}>
                {result.data_delta_gb > 0 ? '+' : ''}{result.data_delta_gb} GB
              </div>
              <div className="text-xs text-db-muted">
                {result.current_data_gb} → {result.new_data_gb} GB{t('sim.perMonth')}
              </div>
            </div>
            <div className="rounded-md p-3 border border-db-border bg-db-bg">
              <div className="text-xs uppercase tracking-wide opacity-90">{t('sim.voice')}</div>
              <div className="text-base font-semibold mt-1">
                {result.new_voice_min === -1
                  ? t('sim.unlimitedF')
                  : result.current_voice_min === -1
                  ? `${result.new_voice_min} ${t('sim.min')}`
                  : `${result.voice_delta_min > 0 ? '+' : ''}${result.voice_delta_min} ${t('sim.min')}`}
              </div>
              <div className="text-xs text-db-muted">
                {fmtVoice(result.current_voice_min)} → {fmtVoice(result.new_voice_min)}
              </div>
            </div>
          </div>

          {result.warning && result.warning.trim() && (
            <div className="flex items-start gap-2 bg-db-yellow/10 border border-db-yellow/40 rounded-md p-3 text-sm text-db-yellow">
              <AlertTriangle size={16} className="shrink-0 mt-0.5" />
              <span className="text-db-text">{result.warning}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
