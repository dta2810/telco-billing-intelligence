import {
  createContext,
  useContext,
  useState,
  useCallback,
  Fragment,
  ReactNode,
} from 'react';
import { en } from './en';
import { es } from './es';

export type Lang = 'en' | 'es';

const DICTS: Record<Lang, Record<string, string>> = { en, es };
const STORAGE_KEY = 'acmetel_lang';

function getInitialLang(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'en' || saved === 'es') return saved;
  } catch {
    /* localStorage unavailable */
  }
  return 'es';
}

type Vars = Record<string, string | number>;

function interpolate(s: string, vars?: Vars): string {
  if (!vars) return s;
  let out = s;
  for (const [k, v] of Object.entries(vars)) {
    out = out.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
  }
  return out;
}

interface I18nCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, vars?: Vars) => string;
}

const Ctx = createContext<I18nCtx | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(getInitialLang);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {
      /* ignore */
    }
  }, []);

  const t = useCallback(
    (key: string, vars?: Vars) => {
      const raw = DICTS[lang][key] ?? DICTS.es[key] ?? key;
      return interpolate(raw, vars);
    },
    [lang]
  );

  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}

export function useI18n(): I18nCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error('useI18n must be used within I18nProvider');
  return c;
}

export function useT() {
  return useI18n().t;
}

/** Append the active language as a query param to an API url. */
export function withLang(url: string, lang: Lang): string {
  return url + (url.includes('?') ? '&' : '?') + `lang=${lang}`;
}

/**
 * Interpolate a translation template that contains `{token}` markers, replacing
 * each marker with a ReactNode (e.g. a <strong> element). Returns an array of
 * nodes safe to render inside JSX. Word order stays correct per language.
 */
export function tParts(template: string, parts: Record<string, ReactNode>): ReactNode[] {
  const tokens = template.split(/(\{[a-zA-Z0-9_]+\})/g);
  return tokens.map((tok, i) => {
    const m = tok.match(/^\{([a-zA-Z0-9_]+)\}$/);
    if (m && parts[m[1]] !== undefined) {
      return <Fragment key={i}>{parts[m[1]]}</Fragment>;
    }
    return <Fragment key={i}>{tok}</Fragment>;
  });
}
