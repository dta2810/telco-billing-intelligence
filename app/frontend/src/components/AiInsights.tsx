import { Sparkles } from 'lucide-react';
import { useT } from '../i18n';

interface Props {
  narrative: string | null;
  loading: boolean;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderMarkdown(md: string): string {
  // escape HTML first (LLM output is untrusted), then apply safe bold/italic markup
  return md
    .split('\n')
    .map((line) => {
      const safe = escapeHtml(line);
      const bold = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      return bold.replace(/_(.+?)_/g, '<em class="text-db-muted">$1</em>');
    })
    .join('<br/>');
}

export function AiInsights({ narrative, loading }: Props) {
  const t = useT();
  return (
    <div className="bg-db-card border border-db-accent/30 rounded-lg p-5 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-brand-gradient" />
      <div className="flex items-center gap-2 mb-3 text-db-accent">
        <Sparkles size={16} />
        <h3 className="text-sm font-semibold uppercase tracking-wide">{t('ai.title')}</h3>
      </div>
      {loading ? (
        <div className="text-db-muted text-sm py-6">{t('ai.generating')}</div>
      ) : narrative ? (
        <div
          className="text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(narrative) }}
        />
      ) : (
        <div className="text-db-muted text-sm">{t('ai.none')}</div>
      )}
    </div>
  );
}
