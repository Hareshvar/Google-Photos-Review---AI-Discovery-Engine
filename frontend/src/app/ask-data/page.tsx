'use client';

import React, { useState } from 'react';
import { sendChatMessage } from '@/lib/api';
import { ChatMessage, Citation } from '@/components/ChatMessage';
import { RefusalCard } from '@/components/RefusalCard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  isRefusal?: boolean;
  refusalReason?: string;
  refusalType?: 'pii_scrubbed' | 'out_of_scope' | 'no_evidence';
}

export default function AskDataPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello! I am your Retrieval Lens research assistant. I can answer questions grounded strictly in our verified dataset of public Google Photos search failure posts.\n\nWhat would you like to investigate?',
      citations: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [sessionCount, setSessionCount] = useState(10);

  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryText?: string) => {
    const text = queryText || input;
    if (!text.trim() || loading || sessionCount <= 0) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInput('');
    setLoading(true);
    setSessionCount((prev) => Math.max(0, prev - 1));

    const historyPayload = messages
      .filter((m) => m.id !== 'welcome' && !m.isRefusal)
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      const res = await sendChatMessage(text, historyPayload);

      if (res.is_refusal || res.status === 'refused') {
        const refusalMsg = res.answer || res.message || 'Question out of scope.';
        setMessages((prev) => [
          ...prev,
          {
            id: `bot-${Date.now()}`,
            role: 'assistant',
            content: refusalMsg,
            isRefusal: true,
            refusalReason: refusalMsg,
            refusalType: res.refusal_type || res.reason || 'out_of_scope',
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `bot-${Date.now()}`,
            role: 'assistant',
            content: res.answer,
            citations: res.citations || [],
            disclaimer: res.sample_disclaimer || res.disclaimer,
          },
        ]);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I encountered an error connecting to the backend RAG engine. Please try again.',
          isRefusal: true,
          refusalReason: 'Backend connectivity failure',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border-subtle shrink-0">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-google-blue-tint text-primary-container text-xs font-semibold mb-1">
            <span className="material-symbols-outlined text-[16px]">chat</span>
            <span>RAG Conversational Assistant</span>
          </div>
          <h1 className="font-headline text-2xl font-semibold text-on-surface tracking-tight">
            Ask the Data
          </h1>
          <p className="text-xs text-on-secondary-container mt-0.5">
            Query the vector database (ChromaDB + Gemini 2.5 Flash) with up to 3 verified quote citations per answer.
          </p>
        </div>

        {/* Question Counter + Disclaimer */}
        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="px-3 py-1.5 rounded-full bg-surface-card border border-border-subtle text-xs text-on-surface font-medium flex items-center gap-1.5 shadow-sm">
            <span className="material-symbols-outlined text-primary-container text-[16px]">help</span>
            <span>{sessionCount} questions remaining</span>
          </div>
        </div>
      </div>

      {/* Main Chat + Citation Detail Panel Split Layout */}
      <div className="flex-1 flex flex-col md:flex-row gap-6 pt-4 overflow-hidden">
        {/* Chat History Container */}
        <div className="flex-1 flex flex-col justify-between bg-surface-card border border-border-subtle rounded-2xl p-4 overflow-hidden shadow-sm">
          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-6">
            {messages.map((m) => (
              <React.Fragment key={m.id}>
                {m.isRefusal ? (
                  <RefusalCard
                    reason={m.refusalReason}
                    refusalType={m.refusalType}
                    onSelectPrompt={(p) => handleSend(p)}
                  />
                ) : (
                  <ChatMessage
                    role={m.role}
                    content={m.content}
                    citations={m.citations}
                    onSelectCitation={(cit) => setSelectedCitation(cit)}
                    disclaimer={
                      m.role === 'assistant' && m.id !== 'welcome'
                        ? (m.disclaimer || 'Answers come only from the public posts we collected (n=916 sample). Not a measure of all Google Photos users.')
                        : undefined
                    }
                  />
                )}
              </React.Fragment>
            ))}

            {loading && (
              <div className="flex items-center gap-3 text-xs text-primary-container font-medium p-3">
                <span className="material-symbols-outlined animate-spin text-[20px]">sync</span>
                <span>Searching vector embeddings &amp; generating grounded response...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Prompt Suggestion Chips */}
          {messages.length <= 2 && (
            <div className="pt-3 border-t border-border-subtle flex flex-col gap-2">
              <span className="text-xs font-semibold text-on-secondary-container">
                Suggested research queries:
              </span>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleSend('What information do people actually remember about a photo?')}
                  className="px-3 py-1.5 rounded-full bg-surface-bg border border-border-subtle text-xs text-on-surface hover:bg-google-blue-tint hover:text-primary-container transition-colors"
                >
                  &ldquo;What information do people actually remember about a photo?&rdquo;
                </button>
                <button
                  onClick={() => handleSend('Which photo types fail search most frequently?')}
                  className="px-3 py-1.5 rounded-full bg-surface-bg border border-border-subtle text-xs text-on-surface hover:bg-google-blue-tint hover:text-primary-container transition-colors"
                >
                  &ldquo;Which photo types fail search most frequently?&rdquo;
                </button>
                <button
                  onClick={() => handleSend('Where in the search flow do users encounter errors?')}
                  className="px-3 py-1.5 rounded-full bg-surface-bg border border-border-subtle text-xs text-on-surface hover:bg-google-blue-tint hover:text-primary-container transition-colors"
                >
                  &ldquo;Where in the search flow do users encounter errors?&rdquo;
                </button>
              </div>
            </div>
          )}

          {/* Input Box */}
          <div className="mt-3 pt-3 border-t border-border-subtle">
            <div className="relative flex items-center">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask a question about user photo retrieval failures..."
                disabled={loading || sessionCount <= 0}
                className="w-full h-12 pl-4 pr-12 bg-surface-bg border border-border-subtle rounded-full text-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:border-primary-container focus:bg-white transition-all disabled:opacity-50"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading || sessionCount <= 0}
                className="absolute right-2 w-9 h-9 rounded-full bg-primary-container text-white flex items-center justify-center hover:bg-[#1557b0] transition-colors disabled:opacity-40"
              >
                <span className="material-symbols-outlined text-[18px]">send</span>
              </button>
            </div>
          </div>
        </div>

        {/* Citation Sidebar Panel */}
        <div className="w-full md:w-80 bg-surface-card border border-border-subtle rounded-2xl p-4 flex flex-col gap-3 shadow-sm shrink-0 overflow-y-auto">
          <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary-container text-[20px]">
                format_quote
              </span>
              <h3 className="font-semibold text-sm text-on-surface">Evidence Inspection</h3>
            </div>
            {selectedCitation && (
              <button
                onClick={() => setSelectedCitation(null)}
                className="text-xs text-on-secondary-container hover:underline"
              >
                Clear
              </button>
            )}
          </div>

          {selectedCitation ? (
            <div className="flex flex-col gap-3 text-xs">
              <div className="p-3 rounded-xl bg-google-blue-tint border border-[#d2e3fc]">
                <span className="font-semibold text-primary-container text-[11px] block mb-1">
                  SOURCE SUBMISSION
                </span>
                <p className="text-on-surface italic font-body text-sm leading-relaxed">
                  &ldquo;{selectedCitation.quote}&rdquo;
                </p>
              </div>

              <div className="flex flex-col gap-1.5 p-3 rounded-xl bg-surface-bg border border-border-subtle text-on-surface">
                <div className="flex justify-between">
                  <span className="text-on-secondary-container">Post ID:</span>
                  <span className="font-mono font-semibold">{selectedCitation.post_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-on-secondary-container">Channel:</span>
                  <span className="font-semibold">{selectedCitation.source}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-on-secondary-container">Date:</span>
                  <span>{selectedCitation.date}</span>
                </div>
              </div>

              {selectedCitation.url && (
                <a
                  href={selectedCitation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="h-9 px-4 rounded-full bg-primary-container text-white font-medium flex items-center justify-center gap-2 hover:bg-[#1557b0] transition-colors"
                >
                  <span>View Original Post</span>
                  <span className="material-symbols-outlined text-[16px]">open_in_new</span>
                </a>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center text-center py-12 text-on-secondary-container gap-2">
              <span className="material-symbols-outlined text-[36px] opacity-40">touch_app</span>
              <p className="text-xs leading-relaxed">
                Click any citation chip inside an answer to inspect its original verbatim quote and source metadata here.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
