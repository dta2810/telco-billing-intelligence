import { Link, useLocation } from 'react-router-dom';
import { Activity, Users, LayoutDashboard, Languages } from 'lucide-react';
import { useI18n, Lang } from '../i18n';

const navItems = [
  { to: '/', key: 'nav.home', icon: LayoutDashboard },
  { to: '/exec', key: 'nav.exec', icon: Activity },
  { to: '/customer', key: 'nav.customer', icon: Users },
];

export function Header() {
  const { pathname } = useLocation();
  const { t, lang, setLang } = useI18n();
  return (
    <header className="border-b border-db-border bg-db-card">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold">
          <span className="text-db-accent">AcmeTel</span>
          <span className="text-db-muted">{t('brand.tagline')}</span>
        </Link>
        <div className="flex items-center gap-3">
          <nav className="flex gap-1">
            {navItems.map(({ to, key, icon: Icon }) => {
              const active = to === '/' ? pathname === '/' : pathname.startsWith(to);
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${
                    active
                      ? 'bg-db-accent/15 text-db-accent'
                      : 'text-db-muted hover:text-db-text hover:bg-db-border/40'
                  }`}
                >
                  <Icon size={16} />
                  {t(key)}
                </Link>
              );
            })}
          </nav>
          <div
            className="flex items-center gap-0.5 border border-db-border rounded-md p-0.5"
            title={t('lang.toggle')}
          >
            <Languages size={14} className="text-db-muted ml-1 mr-0.5" />
            {(['es', 'en'] as Lang[]).map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                className={`px-2 py-0.5 rounded text-xs uppercase font-medium transition-colors ${
                  lang === l
                    ? 'bg-db-accent/15 text-db-accent'
                    : 'text-db-muted hover:text-db-text'
                }`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}
