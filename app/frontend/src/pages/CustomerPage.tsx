import { useSearchParams } from 'react-router-dom';
import { UserSearch } from 'lucide-react';
import { CustomerDetailPanel } from '../components/CustomerDetailPanel';
import { OperationalAlerts } from '../components/OperationalAlerts';
import { CustomerSearchBox } from '../components/CustomerSearchBox';
import { useT } from '../i18n';

export function CustomerPage() {
  const t = useT();
  const [params, setParams] = useSearchParams();
  const selected = params.get('selected');

  const setSelected = (id: string) => {
    const next = new URLSearchParams(params);
    next.set('selected', id);
    setParams(next, { replace: true });
  };

  const clearSelected = () => {
    const next = new URLSearchParams(params);
    next.delete('selected');
    setParams(next, { replace: true });
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-6 space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">{t('cust.title')}</h1>
        <p className="text-db-muted text-sm mt-1">{t('cust.subtitle')}</p>
      </div>

      {/* Operational alerts (top, always visible) */}
      <OperationalAlerts />

      {/* Search */}
      <div className="bg-db-card border border-db-border rounded-lg p-5">
        <h3 className="text-sm font-semibold mb-3">{t('cust.searchCustomer')}</h3>
        <CustomerSearchBox onSelect={setSelected} autoFocus variant="large" />
        <p className="text-xs text-db-muted mt-3 text-center">{t('cust.searchHint')}</p>
      </div>

      {/* Detail */}
      {selected ? (
        <div className="space-y-3">
          <div className="flex justify-end">
            <button
              onClick={clearSelected}
              className="text-xs text-db-muted hover:text-db-text"
            >
              {t('cust.close')}
            </button>
          </div>
          <CustomerDetailPanel key={selected} customerId={selected} />
        </div>
      ) : (
        <div className="bg-db-card border border-db-border rounded-md p-10 text-center">
          <UserSearch size={42} className="mx-auto text-db-accent/40 mb-4" />
          <h3 className="text-base font-semibold mb-1.5">{t('cust.noneSelected')}</h3>
          <p className="text-sm text-db-muted max-w-md mx-auto">
            {t('cust.emptyHintPre')}
            <span className="font-mono text-db-text">CUS-NNNNNN</span>
            {t('cust.emptyHintPost')}
          </p>
        </div>
      )}
    </div>
  );
}
