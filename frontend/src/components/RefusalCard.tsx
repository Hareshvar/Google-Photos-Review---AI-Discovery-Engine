import React from 'react';

interface RefusalCardProps {
  reason?: string;
  refusalType?: 'pii_scrubbed' | 'out_of_scope' | 'no_evidence';
  suggestedPrompts?: string[];
  onSelectPrompt?: (p: string) => void;
}

export const RefusalCard: React.FC<RefusalCardProps> = ({
  reason,
  refusalType = 'out_of_scope',
  suggestedPrompts = [
    'What photo types fail most frequently?',
    'What visual cues do users remember?',
    'Where in the search flow do users encounter errors?'
  ],
  onSelectPrompt,
}) => {
  return (
    <div className="p-5 rounded-2xl bg-google-yellow-tint border border-[#feefc3] text-on-surface shadow-sm flex flex-col gap-3 max-w-3xl mr-auto">
      <div className="flex items-center gap-2 text-[#b06000] font-semibold text-sm">
        <span className="material-symbols-outlined text-[20px]">info</span>
        <span>
          {refusalType === 'pii_scrubbed'
            ? 'Personal Information Detected'
            : refusalType === 'no_evidence'
            ? 'Not Enough Evidence in Dataset'
            : 'Out of Scope Query'}
        </span>
      </div>

      <p className="text-sm text-on-surface leading-relaxed">
        {reason ||
          'Answers can only be derived from public photo retrieval failure posts. We cannot answer queries regarding market share, internal Google systems, or personal user data.'}
      </p>

      {suggestedPrompts.length > 0 && (
        <div className="mt-2 pt-3 border-t border-[#feefc3] flex flex-col gap-2">
          <span className="text-xs font-semibold text-on-secondary-container">
            Try asking one of these answerable questions instead:
          </span>
          <div className="flex flex-wrap gap-2">
            {suggestedPrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => onSelectPrompt && onSelectPrompt(p)}
                className="px-3 py-1.5 rounded-full bg-white border border-[#feefc3] text-xs text-primary-container font-medium hover:bg-google-blue-tint transition-colors text-left"
              >
                &ldquo;{p}&rdquo;
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
