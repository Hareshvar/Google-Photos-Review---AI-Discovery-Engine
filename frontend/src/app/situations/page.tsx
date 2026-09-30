'use client';

import React, { useEffect, useState } from 'react';
import { fetchSituations } from '@/lib/api';
import { SituationsTable, SituationRow } from '@/components/SituationsTable';

export default function SituationsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState<'score' | 'count' | 'unresolved'>('score');

  useEffect(() => {
    fetchSituations().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-primary-container font-medium">
          <span className="material-symbols-outlined animate-spin text-[28px]">sync</span>
          <span>Loading Situations Matrix &amp; Opportunity Scores...</span>
        </div>
      </div>
    );
  }

  const rawSituations: SituationRow[] = data?.situations || [];
  const tailRow: SituationRow | null = data?.tail_aggregated || null;
  const formulaCaption =
    data?.formula_caption ||
    'Share (%) x Avg Severity (1-3) x Unresolved Rate (0-1) scaled to 0-100';

  const sortedSituations = [...rawSituations].sort((a, b) => {
    const aCount = a.post_count ?? a.count ?? 0;
    const bCount = b.post_count ?? b.count ?? 0;
    const aUnres = a.unresolved_rate_pct ?? (a.unresolved_rate != null ? a.unresolved_rate * 100 : 0);
    const bUnres = b.unresolved_rate_pct ?? (b.unresolved_rate != null ? b.unresolved_rate * 100 : 0);
    const aScore = a.opportunity_score ?? 0;
    const bScore = b.opportunity_score ?? 0;

    if (sortField === 'count') return bCount - aCount;
    if (sortField === 'unresolved') return bUnres - aUnres;
    return bScore - aScore;
  });

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-google-blue-tint text-primary-container text-xs font-semibold mb-2">
            <span className="material-symbols-outlined text-[16px]">table_chart</span>
            <span>Composite Situations Analysis</span>
          </div>
          <h1 className="font-headline text-3xl font-semibold text-on-surface tracking-tight">
            User Situations &amp; Opportunity Scores
          </h1>
          <p className="text-sm text-on-secondary-container mt-1">
            Combinations of Photo Target Type × Primary Cue × User Job, prioritized deterministically by business impact.
          </p>
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-2 self-start md:self-auto bg-surface-card border border-border-subtle p-1 rounded-full shadow-sm">
          <span className="text-xs text-on-secondary-container px-3 font-semibold">Sort by:</span>
          <button
            onClick={() => setSortField('score')}
            className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
              sortField === 'score'
                ? 'bg-primary-container text-white'
                : 'text-on-surface hover:bg-surface-container'
            }`}
          >
            Opportunity Score
          </button>
          <button
            onClick={() => setSortField('count')}
            className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
              sortField === 'count'
                ? 'bg-primary-container text-white'
                : 'text-on-surface hover:bg-surface-container'
            }`}
          >
            Post Volume
          </button>
          <button
            onClick={() => setSortField('unresolved')}
            className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
              sortField === 'unresolved'
                ? 'bg-primary-container text-white'
                : 'text-on-surface hover:bg-surface-container'
            }`}
          >
            Unresolved %
          </button>
        </div>
      </div>

      {/* Formula & Demographics Captions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-surface-card border border-border-subtle text-xs text-on-secondary-container flex items-start gap-3 shadow-sm">
          <span className="material-symbols-outlined text-primary-container text-[20px] shrink-0">
            functions
          </span>
          <div>
            <span className="font-semibold text-on-surface block mb-0.5">
              Deterministic Opportunity Score Formula
            </span>
            <span>{formulaCaption}</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-surface-card border border-border-subtle text-xs text-on-secondary-container flex items-start gap-3 shadow-sm">
          <span className="material-symbols-outlined text-google-yellow text-[20px] shrink-0">
            attribution
          </span>
          <div>
            <span className="font-semibold text-on-surface block mb-0.5">
              Demographics Disclaimer
            </span>
            <span>
              These are retrieval situations, not user demographics — public posts do not reveal age, location, or occupation.
            </span>
          </div>
        </div>
      </div>

      {/* Ranked Table */}
      <SituationsTable situations={sortedSituations} tailRow={tailRow} />
    </div>
  );
}
