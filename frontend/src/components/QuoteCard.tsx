import React from 'react';

interface QuoteCardProps {
  quote: string;
  source?: string;
  date?: string;
  url?: string;
  verified?: boolean;
}

export const QuoteCard: React.FC<QuoteCardProps> = ({
  quote,
  source = 'Google Help Community',
  date = '2024-05-12',
  url,
  verified = true,
}) => {
  return (
    <div className="bg-surface-card border border-border-subtle rounded-xl p-4 flex flex-col justify-between shadow-sm hover:border-[#1a73e8] transition-colors">
      <p className="text-sm text-on-surface italic leading-relaxed">
        &ldquo;{quote}&rdquo;
      </p>
      <div className="mt-3 pt-3 border-t border-border-subtle flex items-center justify-between text-xs text-on-secondary-container">
        <div className="flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[16px] text-primary-container">
            forum
          </span>
          <span className="font-medium text-on-surface">{source}</span>
          <span>•</span>
          <span>{date}</span>
        </div>
        <div className="flex items-center gap-2">
          {verified && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#e6f4ea] text-[#137333] font-medium text-[11px]">
              <span className="material-symbols-outlined text-[14px]">check_circle</span>
              Quote Verified
            </span>
          )}
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-container hover:underline flex items-center gap-0.5"
            >
              <span>Link</span>
              <span className="material-symbols-outlined text-[14px]">open_in_new</span>
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
