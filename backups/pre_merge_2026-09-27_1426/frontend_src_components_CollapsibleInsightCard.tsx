import React, { useState } from 'react';
import { QuoteCard } from './QuoteCard';

export interface InsightDistributionItem {
  category?: string;
  label?: string;
  count: number;
  share_pct?: number;
  pct?: number;
}

export interface InsightCardData {
  id: string;
  question_id?: string;
  number?: number;
  question: string;
  evidence_n?: number;
  n_sample?: number;
  is_low_evidence?: boolean;
  low_evidence_warning?: string;
  low_evidence_message?: string;
  summary: string;
  distribution?: InsightDistributionItem[];
  verbatim_queries?: { query: string; count: number }[];
  example_quotes?: any[];
  quotes?: any[];
  kpi_breakage?: { step: string; kpi_impact: string; count: number; pct?: number; share_pct?: number }[];
}

interface CollapsibleInsightCardProps {
  card: InsightCardData;
}

export const CollapsibleInsightCard: React.FC<CollapsibleInsightCardProps> = ({
  card,
}) => {
  const [expanded, setExpanded] = useState(false);

  const sampleSize = card.evidence_n ?? card.n_sample ?? 0;
  const isLowEvidence = (card.is_low_evidence && sampleSize < 3) || sampleSize < 3;
  const isSmallSample = sampleSize >= 3 && sampleSize < 10;
  const qId = card.number ? `Q${card.number}` : (card.question_id || 'Q');

  const rawQuotes = card.quotes || card.example_quotes || [];

  return (
    <div
      className={`border rounded-2xl overflow-hidden transition-all shadow-sm ${
        isLowEvidence
          ? 'bg-google-yellow-tint border-[#feefc3]'
          : 'bg-surface-card border-border-subtle hover:border-[#1a73e8]'
      }`}
    >
      {/* Header Bar */}
      <div
        onClick={() => setExpanded(!expanded)}
        className="p-5 flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-4">
          <span
            className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
              isLowEvidence
                ? 'bg-[#fbbc04] text-[#b06000]'
                : 'bg-google-blue-tint text-primary-container'
            }`}
          >
            {qId}
          </span>
          <div>
            <h3 className="font-headline text-lg font-semibold text-on-surface">
              {card.question}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-on-secondary-container font-medium">
                Sample size: n={sampleSize.toLocaleString()}
              </span>
              {isLowEvidence && (
                <span className="px-2 py-0.5 rounded-full bg-[#fbbc04]/20 text-[#b06000] text-xs font-semibold flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">warning</span>
                  Low Evidence
                </span>
              )}
            </div>
          </div>
        </div>

        <button className="p-2 rounded-full hover:bg-surface-container text-on-surface-variant shrink-0">
          <span className="material-symbols-outlined text-[24px]">
            {expanded ? 'expand_less' : 'expand_more'}
          </span>
        </button>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-5 pb-5 pt-2 border-t border-border-subtle/60 flex flex-col gap-5">
          {/* Low Evidence Warning Box */}
          {isLowEvidence ? (
            <div className="p-4 rounded-xl bg-white/80 border border-[#feefc3] text-[#b06000] flex items-start gap-3">
              <span className="material-symbols-outlined text-[22px] text-[#fbbc04] shrink-0">
                info
              </span>
              <p className="text-sm leading-relaxed">
                {card.low_evidence_warning || card.low_evidence_message ||
                  `There isn't enough evidence in the collected data to answer this confidently (n=${sampleSize}). This should be validated through user research.`}
              </p>
            </div>
          ) : (
            /* LLM Summary Text Box */
            <div className="p-4 rounded-xl bg-surface-bg border border-border-subtle/80 text-sm text-on-surface leading-relaxed font-body shadow-inner">
              <div className="flex items-center gap-2 text-xs font-semibold text-primary-container mb-1">
                <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
                <span>Grounded AI Evidence Synthesis</span>
              </div>
              <p className="text-on-surface/90">{card.summary}</p>
            </div>
          )}

          {/* Distribution Chart / Bars */}
          {!isLowEvidence && card.distribution && card.distribution.length > 0 && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                  Empirical Tag Distribution (% of relevant posts, n={sampleSize.toLocaleString()})
                </h4>
                {isSmallSample && (
                  <span className="text-xs text-on-secondary-container italic font-medium">
                    Based on a small sample (n={sampleSize}).
                  </span>
                )}
              </div>
              <div className="flex flex-col gap-2">
                {card.distribution.map((item, idx) => {
                  const categoryName = item.category || item.label || 'Unknown Category';
                  const percentage = item.share_pct ?? item.pct ?? 0;
                  const postCount = item.count ?? 0;

                  return (
                    <div key={idx} className="flex items-center gap-3 text-xs">
                      <span className="w-56 text-on-surface font-medium truncate shrink-0" title={categoryName}>
                        {categoryName}
                      </span>
                      <div className="flex-1 bg-surface-container rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-primary-container h-3 rounded-full transition-all"
                          style={{ width: `${Math.min(100, Math.max(1, percentage))}%` }}
                        />
                      </div>
                      <span className="w-32 text-right font-semibold text-on-surface shrink-0">
                        {percentage.toFixed(1)}% ({postCount.toLocaleString()} posts)
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Verbatim Queries Table */}
          {!isLowEvidence && card.verbatim_queries && card.verbatim_queries.length > 0 && (
            <div className="flex flex-col gap-2">
              <h4 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                Top Verbatim Quoted Search Queries
              </h4>
              <div className="flex flex-wrap gap-2">
                {card.verbatim_queries.map((q, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 rounded-full bg-surface-bg border border-border-subtle text-xs text-on-surface font-mono"
                  >
                    &ldquo;{q.query}&rdquo; ({q.count})
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* KPI Breakage Table */}
          {!isLowEvidence && card.kpi_breakage && card.kpi_breakage.length > 0 && (
            <div className="flex flex-col gap-2">
              <h4 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                KPI Funnel Stage Impact
              </h4>
              <div className="overflow-x-auto border border-border-subtle rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-surface-bg border-b border-border-subtle text-on-surface-variant">
                    <tr>
                      <th className="p-2.5">Failure Step</th>
                      <th className="p-2.5">KPI Impact Description</th>
                      <th className="p-2.5 text-right">Posts</th>
                      <th className="p-2.5 text-right">Share %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle">
                    {card.kpi_breakage.map((kpi, idx) => {
                      const kpiPct = kpi.share_pct ?? kpi.pct ?? 0;
                      return (
                        <tr key={idx} className="hover:bg-surface-container-low">
                          <td className="p-2.5 font-semibold text-on-surface">{kpi.step}</td>
                          <td className="p-2.5 text-on-secondary-container">{kpi.kpi_impact}</td>
                          <td className="p-2.5 text-right font-medium">{kpi.count.toLocaleString()}</td>
                          <td className="p-2.5 text-right font-semibold text-primary-container">{kpiPct.toFixed(1)}%</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Supporting Quotes */}
          {rawQuotes.length > 0 && (
            <div className="flex flex-col gap-2 pt-2 border-t border-border-subtle/40">
              <h4 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                Verbatim Evidence Quotes
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {rawQuotes.map((q, qIdx) => {
                  const quoteText = typeof q === 'string' ? q : (q.quote || q.title || '');
                  const source = typeof q === 'object' && q.source ? q.source : undefined;
                  const url = typeof q === 'object' && q.url ? q.url : undefined;
                  return (
                    <QuoteCard 
                      key={qIdx} 
                      quote={quoteText} 
                      source={source}
                      url={url}
                      verified={true} 
                    />
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

