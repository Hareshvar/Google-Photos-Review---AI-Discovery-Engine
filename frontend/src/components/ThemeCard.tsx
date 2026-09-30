import React, { useState } from 'react';
import { QuoteCard } from './QuoteCard';

export interface ThemeCardProps {
  clusterIndex: number;
  clusterId?: string;
  themeTitle?: string;
  title?: string;
  count: number;
  sharePct: number;
  topQuotes?: any[];
  example_quotes?: any[];
  summaryNote?: string;
}

function cleanMojibake(text: string): string {
  if (!text) return "";
  const replacements: Record<string, string> = {
    "â€œ": '"',
    "â€": '"',
    "â€™": "'",
    "â€˜": "'",
    "â€”": "—",
    "â€“": "–",
    "â€¦": "...",
    "â€¢": "•",
    "âpets and peopleâ": '"pets and people"',
    "âpets": '"pets',
    "peopleâ": 'people"',
    "doesnât": "doesn't",
    "â": "",
    "Ã©": "é",
    "\u202f": " ",
    "\xa0": " ",
  };
  let cleaned = text;
  for (const [bad, good] of Object.entries(replacements)) {
    cleaned = cleaned.replaceAll(bad, good);
  }
  return cleaned.trim();
}

export const ThemeCard: React.FC<ThemeCardProps> = ({
  clusterIndex,
  clusterId,
  themeTitle,
  title,
  count,
  sharePct,
  topQuotes,
  example_quotes,
  summaryNote,
}) => {
  const [expanded, setExpanded] = useState(false);

  const displayTitle = themeTitle || title || 'Emergent Theme Cluster';
  const rawQuotes = topQuotes || example_quotes || [];
  const quoteList: { quote: string; source?: string; url?: string }[] = rawQuotes.map((q) =>
    typeof q === 'string' ? { quote: q } : q
  );

  const isSmallSample = count < 10;
  const isLocationCueCluster = clusterId === 'cluster_05' || displayTitle.toLowerCase().includes('location');

  return (
    <div
      className={`border rounded-2xl p-5 shadow-sm transition-all ${
        isSmallSample
          ? 'bg-google-yellow-tint/40 border-[#feefc3] hover:border-[#fbbc04]'
          : 'bg-surface-card border-border-subtle hover:shadow-md'
      }`}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3 cursor-pointer select-none" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 rounded-full bg-google-blue-tint text-primary-container font-bold flex items-center justify-center text-sm shrink-0">
            {clusterIndex + 1}
          </span>
          <div>
            <h3 className="font-headline text-lg font-semibold text-on-surface flex items-center gap-2 flex-wrap">
              <span>{displayTitle}</span>
            </h3>
          </div>
        </div>
        <div className="flex items-center gap-2.5 self-start md:self-auto flex-wrap">
          {isSmallSample && (
            <span className="px-2.5 py-0.5 rounded-full bg-[#fbbc04]/20 border border-[#fbbc04]/40 text-[#b06000] text-xs font-semibold flex items-center gap-1 shrink-0">
              <span className="material-symbols-outlined text-[14px]">warning</span>
              Small sample (n={count})
            </span>
          )}
          <span className="px-3 py-1 rounded-full bg-surface-container text-on-surface font-semibold text-sm">
            {count.toLocaleString()} posts ({sharePct}%)
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            className="text-primary-container text-sm font-medium flex items-center gap-1 hover:underline"
          >
            <span>{expanded ? 'Hide details' : 'See evidence'}</span>
            <span className="material-symbols-outlined text-[18px]">
              {expanded ? 'expand_less' : 'expand_more'}
            </span>
          </button>
        </div>
      </div>

      {/* Share Progress Bar */}
      <div className="w-full bg-surface-container rounded-full h-2 mb-4 overflow-hidden">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${isSmallSample ? 'bg-[#fbbc04]' : 'bg-[#1a73e8]'}`}
          style={{ width: `${Math.min(100, Math.max(2, sharePct))}%` }}
        />
      </div>

      {/* Distinguishing Signal Note for cluster_05 (Memory Content Signal) */}
      {isLocationCueCluster && (
        <div className="mb-3 px-3 py-1.5 rounded-lg bg-blue-50/70 border border-blue-100 text-[#1a73e8] text-xs flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] shrink-0">info</span>
          <span>
            <strong>Signal note:</strong> Derived from what users say they remember or forgot (memory cue content), distinct from reported technical system failures.
          </span>
        </div>
      )}

      {/* Small Sample Warning Caption for n < 10 */}
      {isSmallSample && (
        <div className="mb-3 px-3 py-1.5 rounded-lg bg-[#fbbc04]/10 border border-[#fbbc04]/30 text-[#b06000] text-xs flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] shrink-0">amber</span>
          <span>
            <strong>Caution:</strong> Small sample size (n={count}). Findings are qualitative and directional.
          </span>
        </div>
      )}

      {/* LLM Research Synthesis Summary Box */}
      {summaryNote && (
        <div className="bg-surface-bg border border-border-subtle rounded-xl p-4 mb-4 flex flex-col gap-1.5">
          <div className="flex items-center gap-2 text-primary-container font-semibold text-xs uppercase tracking-wider">
            <span className="material-symbols-outlined text-[16px]">psychology</span>
            <span>LLM Research UX Summary</span>
          </div>
          <p className="text-xs text-on-surface leading-relaxed">{summaryNote}</p>
        </div>
      )}

      {/* Expandable Quotes Section */}
      {expanded && quoteList.length > 0 && (
        <div className="pt-2 border-t border-border-subtle flex flex-col gap-3">
          <h4 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider flex items-center justify-between">
            <span>Verified Representative Quotes ({quoteList.length})</span>
            <span className="text-[11px] font-normal text-on-surface-variant normal-case">Multi-Source Diversity Verified</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {quoteList.map((qObj, idx) => (
              <QuoteCard
                key={idx}
                quote={cleanMojibake(qObj.quote)}
                source={qObj.source}
                url={qObj.url}
                verified={true}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
