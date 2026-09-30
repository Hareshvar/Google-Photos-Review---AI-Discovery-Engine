import React from 'react';

export interface Citation {
  post_id: string;
  source: string;
  url: string;
  date: string;
  quote: string;
}

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  onSelectCitation?: (cit: Citation) => void;
  disclaimer?: string;
}

export const CitationChip: React.FC<{
  index: number;
  citation: Citation;
  onClick?: () => void;
}> = ({ index, citation, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-google-blue-tint text-primary-container border border-[#d2e3fc] text-xs font-semibold hover:bg-white transition-colors shadow-sm"
      title={`Click to view citation #${index + 1}`}
    >
      <span className="material-symbols-outlined text-[14px]">format_quote</span>
      <span>Quote #{index + 1}</span>
      <span className="text-[10px] text-on-secondary-container">({citation.source})</span>
    </button>
  );
};

const renderFormattedContent = (text: string) => {
  if (!text) return null;
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
};

export const ChatMessage: React.FC<ChatMessageProps> = ({
  role,
  content,
  citations = [],
  onSelectCitation,
  disclaimer,
}) => {
  const isUser = role === 'user';

  return (
    <div
      className={`flex flex-col gap-2 max-w-3xl ${
        isUser ? 'ml-auto items-end' : 'mr-auto items-start'
      }`}
    >
      {/* Avatar + Name Header */}
      <div className="flex items-center gap-2 text-xs font-semibold text-on-secondary-container">
        {isUser ? (
          <>
            <span>Researcher</span>
            <div className="w-6 h-6 rounded-full bg-surface-container text-on-surface flex items-center justify-center">
              <span className="material-symbols-outlined text-[14px]">person</span>
            </div>
          </>
        ) : (
          <>
            <div className="w-6 h-6 rounded-full bg-google-blue-tint text-primary-container flex items-center justify-center">
              <span className="material-symbols-outlined text-[14px]">psychology</span>
            </div>
            <span>Retrieval Lens RAG</span>
          </>
        )}
      </div>

      {/* Bubble */}
      <div
        className={`p-4 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-primary-container text-white rounded-tr-none'
            : 'bg-surface-card border border-border-subtle text-on-surface rounded-tl-none shadow-sm'
        }`}
      >
        <p className="whitespace-pre-line">{renderFormattedContent(content)}</p>


        {/* Inline Citation Chips */}
        {!isUser && citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border-subtle flex flex-wrap gap-2">
            <span className="text-xs font-semibold text-on-surface-variant w-full">
              Verified Quote Citations ({citations.length}):
            </span>
            {citations.map((cit, idx) => (
              <CitationChip
                key={idx}
                index={idx}
                citation={cit}
                onClick={() => onSelectCitation && onSelectCitation(cit)}
              />
            ))}
          </div>
        )}

        {/* Disclaimer Banner */}
        {!isUser && disclaimer && (
          <p className="mt-3 text-[11px] italic text-on-secondary-container leading-tight">
            {disclaimer}
          </p>
        )}
      </div>
    </div>
  );
};
