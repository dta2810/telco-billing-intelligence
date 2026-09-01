import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, RotateCcw } from 'lucide-react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { useI18n } from '../i18n';

marked.setOptions({ gfm: true, breaks: true });

interface QueryResult {
  columns: string[];
  rows: string[][];
}

interface Message {
  role: 'user' | 'agent';
  content: string;
  supervisorAnswer?: string;
  genieQuery?: string | null;
  genieRawReply?: string;
  queryResult?: QueryResult | null;
}

interface GenieChatProps {
  context: string;             // shown next to the title (e.g. "datos del portafolio")
  suggestedQuestions: string[];
  customerId?: string;         // optional scope sent to supervisor
  height?: string | number;    // tailwind height or px
  useMemory?: boolean;         // customer-360: route to the memory agent (short+long-term memory)
}

function renderMd(s: string): string {
  // marked.parse returns string in sync mode (default); sanitize LLM/Genie output before render
  return DOMPurify.sanitize(marked.parse(s) as string);
}

export function GenieChat({ context, suggestedQuestions, customerId, height = 540, useMemory = false }: GenieChatProps) {
  const { t, lang } = useI18n();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // New subscriber selected → start a fresh session (new memory thread, clear transcript).
  useEffect(() => {
    setMessages([]);
    setConversationId(null);
    setThreadId(null);
  }, [customerId]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg = text.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      if (useMemory) {
        // Customer-360: memory agent (short + long-term memory), scoped to the subscriber.
        const res = await fetch('/api/memory/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMsg,
            thread_id: threadId,
            customer_id: customerId,
            lang,
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${res.status}`);
        }
        const data = await res.json();
        if (data.thread_id) setThreadId(data.thread_id);
        setMessages((prev) => [
          ...prev,
          { role: 'agent', content: data.answer || t('genie.noAnswer') },
        ]);
      } else {
        const res = await fetch('/api/agent/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMsg,
            conversation_id: conversationId,
            customer_id: customerId,
            lang,
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${res.status}`);
        }
        const data = await res.json();
        setConversationId(data.conversation_id);
        setMessages((prev) => [
          ...prev,
          {
            role: 'agent',
            content: data.supervisor_answer || data.genie_raw_reply || t('genie.noAnswer'),
            supervisorAnswer: data.supervisor_answer,
            genieQuery: data.genie_query,
            genieRawReply: data.genie_raw_reply,
            queryResult: data.genie_data,
          },
        ]);
      }
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : t('genie.unknownError');
      setMessages((prev) => [...prev, { role: 'agent', content: `${t('common.error')}: ${errMsg}` }]);
    } finally {
      setLoading(false);
    }
  };

  const resetChat = () => {
    setMessages([]);
    setConversationId(null);
    setThreadId(null);
  };

  const heightStyle = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className="bg-db-card border border-db-border rounded-lg overflow-hidden flex flex-col"
      style={{ height: heightStyle }}
    >
      {/* Header */}
      <div className="px-5 py-3 border-b border-db-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-db-accent" />
          <h3 className="text-sm font-semibold">{t('genie.assistant')}</h3>
          <span className="text-xs text-db-muted">— {context}</span>
        </div>
        {messages.length > 0 && (
          <button
            onClick={resetChat}
            className="text-xs text-db-muted hover:text-db-text flex items-center gap-1 transition-colors"
          >
            <RotateCcw size={12} /> {t('genie.newQuery')}
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center py-6">
            <Sparkles size={28} className="mx-auto mb-3 text-db-accent/30" />
            <p className="text-sm text-db-muted mb-4">
              {t('genie.askAbout', { context })}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {suggestedQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-left text-xs text-db-muted hover:text-db-accent bg-db-bg border border-db-border hover:border-db-accent/40 rounded-md px-3 py-2 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[88%] rounded-lg px-4 py-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-db-accent text-white rounded-br-sm'
                  : 'bg-db-bg border border-db-border text-db-text rounded-bl-sm'
              }`}
            >
              {msg.role === 'agent' ? (
                <div>
                  <div
                    className="leading-relaxed prose-genie"
                    dangerouslySetInnerHTML={{ __html: renderMd(msg.supervisorAnswer || msg.content) }}
                  />

                  {(msg.genieQuery || msg.queryResult) && (
                    <details className="mt-3 border-t border-db-border/60 pt-2">
                      <summary className="text-xs text-db-accent cursor-pointer hover:opacity-80 select-none py-1">
                        {t('genie.viewData')}
                      </summary>
                      <div className="mt-2 space-y-3">
                        {msg.genieQuery && (
                          <div>
                            <p className="text-xs text-db-muted mb-1">{t('genie.genieQuery')}</p>
                            <pre className="bg-db-border/40 rounded p-2 text-xs font-mono overflow-x-auto whitespace-pre-wrap text-db-text">
                              <code>{msg.genieQuery}</code>
                            </pre>
                          </div>
                        )}
                        {msg.queryResult && (
                          <div className="overflow-x-auto">
                            <p className="text-xs text-db-muted mb-1">{t('genie.results', { n: msg.queryResult.rows.length })}</p>
                            <table className="w-full text-xs border-collapse">
                              <thead>
                                <tr>
                                  {msg.queryResult.columns.map((col) => (
                                    <th key={col} className="text-left px-2 py-1.5 border-b border-db-border text-db-muted font-medium">
                                      {col}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {msg.queryResult.rows.map((row, ri) => (
                                  <tr key={ri} className="border-b border-db-border/40">
                                    {row.map((cell, ci) => (
                                      <td key={ci} className="px-2 py-1.5 text-db-text">{cell}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </details>
                  )}
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-db-bg border border-db-border rounded-lg px-4 py-3 rounded-bl-sm flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-db-accent" />
              <span className="text-sm text-db-muted">{t('genie.analyzing')}</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-5 py-3 border-t border-db-border shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t('genie.placeholder')}
            disabled={loading}
            className="flex-1 bg-db-bg border border-db-border rounded-md px-3 py-2 text-sm text-db-text placeholder:text-db-muted focus:outline-none focus:border-db-accent/50 disabled:opacity-50 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-db-accent hover:bg-accent-soft disabled:opacity-50 disabled:cursor-not-allowed text-white px-3 rounded-md transition-colors"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
