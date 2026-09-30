'use client';

import React, { useEffect, useState } from 'react';
import { fetchThemes } from '@/lib/api';
import { HeatmapChart } from '@/components/HeatmapChart';
import { ThemeCard } from '@/components/ThemeCard';

export default function ThemesPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchThemes().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-primary-container font-medium">
          <span className="material-symbols-outlined animate-spin text-[28px]">sync</span>
          <span>Loading Themes &amp; Failure Matrix...</span>
        </div>
      </div>
    );
  }

  const matrix = data?.layer_a_struggle_matrix || [];
  const clusters = data?.layer_b_emergent_clusters || [];
  const residual = data?.residual_disclosure || { unclassified_count: 36, unclassified_pct: 8.4 };

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-google-blue-tint text-primary-container text-xs font-semibold mb-2">
          <span className="material-symbols-outlined text-[16px]">bubble_chart</span>
          <span>Dual-Layer Themes Analysis</span>
        </div>
        <h1 className="font-headline text-3xl font-semibold text-on-surface tracking-tight">
          Where Search Breaks &amp; Emergent Intent Themes
        </h1>
        <p className="text-sm text-on-secondary-container mt-1">
          Separately analyzing systemic failure points (Section A) and narrative intent clusters (Section B).
        </p>
      </div>

      {/* Section A: Heatmap */}
      <HeatmapChart matrix={matrix} totalRelevant={data?.metadata?.total_relevant || 9737} />

      {/* Section B: Emergent Clusters */}
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="font-headline text-xl text-on-surface font-semibold">
            Section B — Emergent Narrative Intent Clusters
          </h2>
          <p className="text-xs text-on-secondary-container mt-0.5">
            Theme groups identified by matching system issues, primary cues, and keywords. A post can belong to more than one group.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {clusters.map((c: any, idx: number) => (
            <ThemeCard
              key={idx}
              clusterIndex={idx}
              clusterId={c.cluster_id}
              themeTitle={c.title || c.theme_title}
              count={c.count}
              sharePct={c.share_pct}
              example_quotes={c.example_quotes || c.top_quotes}
              summaryNote={c.summary_note}
            />
          ))}
        </div>

        {/* Section 4.3 Residual Bucket Exclusion Footnote */}
        <div className="p-4 rounded-xl bg-surface-card border border-border-subtle text-xs text-on-secondary-container flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-on-surface-variant">info</span>
            <span>
              <strong>Small Sample / Residual Disclosure:</strong> {residual.unclassified_count} posts ({residual.unclassified_pct}%) did not fit an emergent cluster or had unclear system issues.
            </span>
          </div>
          <span className="italic text-[11px]">Excluded from ranked charts per Section 4.3 rule</span>
        </div>
      </div>
    </div>
  );
}
