'use client';

import React, { useEffect, useState } from 'react';
import { fetchInsights } from '@/lib/api';
import { CollapsibleInsightCard, InsightCardData } from '@/components/CollapsibleInsightCard';

export default function InsightsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsights().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-primary-container font-medium">
          <span className="material-symbols-outlined animate-spin text-[28px]">sync</span>
          <span>Loading 9 Key Research Insights...</span>
        </div>
      </div>
    );
  }

  const cards: InsightCardData[] = data?.key_insights || [];

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-google-blue-tint text-primary-container text-xs font-semibold mb-2">
          <span className="material-symbols-outlined text-[16px]">lightbulb</span>
          <span>9 PRD Research Questions</span>
        </div>
        <h1 className="font-headline text-3xl font-semibold text-on-surface tracking-tight">
          Key Research Insights &amp; Evidence Syntheses
        </h1>
        <p className="text-sm text-on-secondary-container mt-1">
          Click any research question below to expand empirical distributions, verbatim quotes, and grounded AI summaries.
        </p>
      </div>

      {/* Accordion Cards Grid */}
      <div className="flex flex-col gap-4">
        {cards.map((card, idx) => (
          <CollapsibleInsightCard key={card.id || idx} card={card} />
        ))}
      </div>
    </div>
  );
}
