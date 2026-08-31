import { Sparkles } from 'lucide-react';
import { useT } from '../i18n';

interface Props {
  narrative: string | null;
  loading: boolean;
}

function renderMarkdown(md: string): string {
  return md
    .split('\n')
    .map((line) => {
      const bold = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      const italic = bold.replace(/_(.+?)_/g, '<em class="text-db-muted">$1</em>');
      return italic;
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
