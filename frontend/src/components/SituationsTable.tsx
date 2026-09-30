import React, { useState } from 'react';
import { QuoteCard } from './QuoteCard';

export interface SituationRow {
  target_type?: string;
  primary_cue?: string;
  job?: string;
  situation_title?: string;
  situation_subtitle?: string;
  situation_name?: string;
  situation_label?: string;
  label?: string;
  post_count?: number;
  count?: number;
  share_pct?: number;
  avg_severity?: number;
  severity?: number;
  unresolved_rate_pct?: number;
  unresolved_rate?: number;
  opportunity_score?: number;
  quotes?: string[];
  example_quotes?: any[];
  is_tail?: boolean;
}

interface SituationsTableProps {
  situations: SituationRow[];
  tailRow?: SituationRow | null;
}

export const SituationsTable: React.FC<SituationsTableProps> = ({
  situations,
  tailRow,
}) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const renderSeverity = (sev?: number) => {
    if (sev == null || isNaN(sev)) {
      return <span className="text-xs text-on-secondary-container">—</span>;
    }
    const level = Math.round(sev);
    return (
      <div className="flex items-center gap-1" title={`Avg Severity: ${sev.toFixed(1)}/3`}>
        <span
          className={`w-2.5 h-2.5 rounded-full ${
            level >= 1 ? 'bg-google-yellow' : 'bg-surface-container-high'
          }`}
        />
        <span
          className={`w-2.5 h-2.5 rounded-full ${
            level >= 2 ? 'bg-google-red' : 'bg-surface-container-high'
          }`}
        />
        <span
          className={`w-2.5 h-2.5 rounded-full ${
            level >= 3 ? 'bg-google-red' : 'bg-surface-container-high'
          }`}
        />
        <span className="text-xs text-on-secondary-container ml-1">
          {level === 1 ? 'Low' : level === 2 ? 'Med' : 'High'}
        </span>
      </div>
    );
  };

  const renderOpportunityBar = (score?: number) => {
    if (score == null) {
      return <span className="text-xs text-on-secondary-container">—</span>;
    }
    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-surface-container rounded-full h-2 overflow-hidden w-24">
          <div
            className="h-2 rounded-full bg-primary-container transition-all"
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </div>
        <span className="font-bold text-sm text-on-surface w-8 text-right">
          {Math.round(score)}
        </span>
      </div>
    );
  };

  const allRows = tailRow ? [...situations, { ...tailRow, is_tail: true }] : situations;

  return (
    <div className="bg-surface-card border border-border-subtle rounded-2xl overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-bg border-b border-border-subtle text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              <th className="py-3.5 px-4">Rank</th>
              <th className="py-3.5 px-4">Situation Context</th>
              <th className="py-3.5 px-4 text-right">Posts (Share %)</th>
              <th className="py-3.5 px-4">Avg Severity</th>
              <th className="py-3.5 px-4 text-right">Unresolved %</th>
              <th className="py-3.5 px-4">Opportunity Score (0-100)</th>
              <th className="py-3.5 px-4 text-center">Evidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle text-sm text-on-surface">
            {allRows.map((row, idx) => {
              const isTail = row.is_tail;
              const isExpanded = expandedIndex === idx;

              const postCount = row.post_count ?? row.count ?? 0;
              const sharePct = row.share_pct ?? 0;
              const severityVal = row.avg_severity ?? row.severity;
              const unresolvedPct =
                row.unresolved_rate_pct ??
                (row.unresolved_rate != null
                  ? Math.round(row.unresolved_rate <= 1 ? row.unresolved_rate * 100 : row.unresolved_rate)
                  : 0);

              const mainTitle =
                row.situation_title ||
                row.situation_name ||
                row.situation_label ||
                row.label ||
                'Retrieval Situation';

              const subTitle =
                row.situation_subtitle ||
                (!isTail && row.target_type
                  ? `Target: ${row.target_type} · Cue: ${row.primary_cue} · Job: ${row.job}`
                  : null);

              const quoteList: { quote: string; source?: string; url?: string }[] = row.quotes
                ? row.quotes.map((q) => (typeof q === 'string' ? { quote: q } : q))
                : Array.isArray(row.example_quotes)
                ? row.example_quotes.map((q) => (typeof q === 'string' ? { quote: q } : q))
                : [];

              return (
                <React.Fragment key={idx}>
                  <tr
                    className={`transition-colors ${
                      isTail
                        ? 'bg-surface-bg text-on-secondary-container italic'
                        : 'hover:bg-surface-container-low'
                    }`}
                  >
                    <td className="py-4 px-4 font-semibold">
                      {isTail ? '—' : `#${idx + 1}`}
                    </td>
                    <td className="py-4 px-4 max-w-md">
                      <div className="font-semibold text-on-surface text-sm leading-snug">
                        {mainTitle}
                      </div>
                      {!isTail && subTitle && (
                        <div className="text-xs text-on-surface-variant mt-1 font-sans">
                          {subTitle}
                        </div>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right font-medium">
                      {postCount} ({sharePct}%)
                    </td>
                    <td className="py-4 px-4">{renderSeverity(severityVal)}</td>
                    <td className="py-4 px-4 text-right font-medium">
                      {unresolvedPct}%
                    </td>
                    <td className="py-4 px-4">
                      {renderOpportunityBar(row.opportunity_score)}
                    </td>
                    <td className="py-4 px-4 text-center">
                      {quoteList.length > 0 ? (
                        <button
                          onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                          className="p-1 rounded-full hover:bg-surface-container text-primary-container"
                        >
                          <span className="material-symbols-outlined text-[20px]">
                            {isExpanded ? 'expand_less' : 'expand_more'}
                          </span>
                        </button>
                      ) : (
                        <span className="text-xs text-on-secondary-container">—</span>
                      )}
                    </td>
                  </tr>

                  {isExpanded && quoteList.length > 0 && (
                    <tr className="bg-surface-container-lowest">
                      <td colSpan={7} className="p-4 border-b border-border-subtle">
                        <div className="flex flex-col gap-2">
                          <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                            Supporting Verbatim Quotes ({quoteList.length})
                          </span>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {quoteList.map((qObj, qIdx) => (
                              <QuoteCard
                                key={qIdx}
                                quote={qObj.quote}
                                source={qObj.source}
                                url={qObj.url}
                                verified={true}
                              />
                            ))}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

