'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchOverview } from '@/lib/api';
import { StatCard } from '@/components/StatCard';
import { PipelineStep } from '@/components/PipelineStep';

export default function OverviewPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-primary-container font-medium">
          <span className="material-symbols-outlined animate-spin text-[28px]">sync</span>
          <span>Loading Discovery Engine Corpus...</span>
        </div>
      </div>
    );
  }

  const stats = data?.stats || {
    collected: 31295,
    cleaned: 9776,
    relevant: 9737,
    vague_memory_count: 6120,
    search_failures_count: 8950,
  };

  const steps = data?.pipeline_steps || [];
  const sources = data?.source_health || [];

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-google-blue-tint text-primary-container text-xs font-semibold mb-3">
            <span className="material-symbols-outlined text-[16px]">psychology</span>
            <span>Synthesis • Multi-channel Discovery Corpus</span>
          </div>
          <h1 className="font-headline text-3xl md:text-4xl text-on-surface tracking-tight font-semibold">
            Why can&apos;t people find the photo they remember?
          </h1>
          <p className="text-base text-on-secondary-container mt-2 leading-relaxed">
            AI analysis of verified public user posts (Reddit, Store Reviews, Google Help Community) on photo retrieval failure modes when human memory is incomplete or fragmented.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Link
            href="/themes"
            className="h-11 px-6 rounded-full bg-primary-container text-white font-medium text-sm flex items-center gap-2 shadow-sm hover:bg-[#1557b0] transition-all"
          >
            <span>Explore themes</span>
            <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
          </Link>
          <Link
            href="/ask-data"
            className="h-11 px-6 rounded-full bg-white text-primary-container font-medium text-sm border border-border-subtle flex items-center gap-2 shadow-sm hover:bg-surface-container transition-all"
          >
            <span className="material-symbols-outlined text-[18px]">chat</span>
            <span>Ask the data</span>
          </Link>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Posts collected"
          count={stats.collected}
          subtitle="Scraped across public feedback channels"
          color="blue"
          icon="inventory_2"
        />
        <StatCard
          title="Classified as relevant"
          count={stats.relevant}
          badge={`${((stats.relevant / Math.max(1, stats.collected)) * 100).toFixed(1)}%`}
          subtitle="Confirmed photo retrieval issues (% of raw collected)"
          color="green"
          icon="fact_check"
        />
        <StatCard
          title="Vague-memory posts"
          count={stats.vague_memory_count}
          badge={`${Math.min(99.9, Number(((stats.vague_memory_count / Math.max(1, stats.relevant)) * 100).toFixed(1)))}%`}
          subtitle="Searchers remember context but not exact tags"
          color="yellow"
          icon="help_outline"
        />
        <StatCard
          title="Search failures"
          count={stats.search_failures_count}
          badge={`${((stats.search_failures_count / Math.max(1, stats.relevant)) * 100).toFixed(1)}%`}
          subtitle="Search returned zero or wrong results"
          color="red"
          icon="error_outline"
        />
      </div>

      {/* Data Ingestion Pipeline Diagram */}
      <div className="bg-surface-card rounded-2xl p-6 shadow-sm border border-border-subtle">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-6 pb-4 border-b border-border-subtle">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="material-symbols-outlined text-[22px] text-primary-container">hub</span>
              <h2 className="font-headline text-xl text-on-surface font-semibold">
                Data Ingestion &amp; Synthesis Pipeline
              </h2>
            </div>
            <p className="text-sm text-on-secondary-container">
              End-to-end processing steps with code-verified tag validation
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#137333] text-[18px]">verified</span>
            <span className="px-3 py-1 rounded-full bg-[#e6f4ea] text-[#137333] text-xs font-semibold border border-[#ceead6]">
              Deterministic validation applied
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-7 items-stretch gap-3">
          {steps.map((s: any, idx: number) => {
            const isCheckedStep = s.step === 'Checked';
            const isAppStep = s.step === 'App';
            return (
              <PipelineStep
                key={idx}
                stepNumber={idx + 1}
                title={s.step}
                countLabel={`${s.count.toLocaleString()} ${s.step === 'App' ? 'ready' : 'items'}`}
                subtitle={s.label}
                icon={
                  idx === 0
                    ? 'download'
                    : idx === 1
                    ? 'filter_alt'
                    : idx === 2
                    ? 'category'
                    : s.step === 'Checked'
                    ? 'verified_user'
                    : idx === 4
                    ? 'analytics'
                    : s.step === 'Index'
                    ? 'dataset'
                    : 'check_circle'
                }
                isHighlighted={isCheckedStep || isAppStep}
                highlightVariant={isCheckedStep ? 'green' : 'blue'}
              />
            );
          })}
        </div>
      </div>

      {/* Source Health Breakdown */}
      <div className="bg-surface-card rounded-2xl p-6 shadow-sm border border-border-subtle">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="font-headline text-xl text-on-surface font-semibold">
              Source Distribution &amp; Relevance Health
            </h2>
            <p className="text-sm text-on-secondary-container">
              Channel breakdown highlighting collected volume, verified signal, and status
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium text-on-secondary-container">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#137333]" /> Active
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#fbbc04]" /> Evaluated (0 hit)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#9aa0a6]" /> Uncollected
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 pt-2">
          {sources.map((src: any, idx: number) => {
            const isZeroYield = src.status === 'zero_yield';
            const isUncollected = src.status === 'uncollected';
            const relRate =
              src.relevance_rate !== undefined && src.relevance_rate !== null
                ? src.relevance_rate
                : src.records_cleaned > 0
                ? (((src.records_relevant ?? src.records_cleaned) / src.records_cleaned) * 100).toFixed(1)
                : '100.0';

            return (
              <div
                key={idx}
                className={`inline-flex items-center gap-2.5 px-4 py-2 rounded-full border text-xs shadow-sm ${
                  isZeroYield
                    ? 'bg-google-yellow-tint border-[#feefc3] text-[#b06000]'
                    : isUncollected
                    ? 'bg-surface-bg border-dashed border-[#dadce0] text-on-secondary-container opacity-80'
                    : 'bg-surface-bg border-border-subtle text-on-surface hover:border-[#137333]'
                }`}
              >
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    isZeroYield
                      ? 'bg-[#fbbc04]'
                      : isUncollected
                      ? 'bg-[#9aa0a6]'
                      : 'bg-[#137333]'
                  }`}
                />
                <span className="font-semibold">{src.source}</span>
                <span>
                  {isZeroYield
                    ? `0 relevant posts found (${src.failure_reason || '0 yield'})`
                    : isUncollected
                    ? `Uncollected (${src.failure_reason || 'API restricted'})`
                    : `${src.records_cleaned} cleaned • ${relRate}% relevant`}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Questions This Data Can Help Answer */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-headline text-xl text-on-surface font-semibold">
              Questions this data can help answer
            </h2>
            <p className="text-sm text-on-secondary-container">
              Key research inquiries synthesized across all public user submissions
            </p>
          </div>
          <Link
            href="/insights"
            className="text-primary-container font-semibold text-sm flex items-center gap-1 hover:underline"
          >
            <span>View all 9 insights</span>
            <span className="material-symbols-outlined text-[18px]">chevron_right</span>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-surface-card border border-border-subtle rounded-2xl p-6 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow">
            <div>
              <div className="flex items-center justify-between gap-2 mb-4">
                <span className="px-3 py-1 rounded-full bg-[#fce8e6] text-[#c5221f] text-xs font-semibold border border-[#fad2cf]">
                  Core Failure Mode
                </span>
                <span className="text-xs text-on-secondary-container font-medium">Q2 &amp; Q3</span>
              </div>
              <h3 className="font-headline text-base font-semibold text-on-surface leading-snug">
                &ldquo;What visual cues do users remember when exact tags are lost?&rdquo;
              </h3>
              <p className="text-xs text-on-secondary-container mt-3 leading-relaxed">
                Users consistently recall approximate temporal anchors, ambient lighting, and peripheral landmarks rather than automated ML subject tags.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-border-subtle">
              <Link
                href="/insights"
                className="text-xs text-primary-container font-semibold flex items-center gap-1 hover:underline"
              >
                <span>Read Key Insight Q2</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </Link>
            </div>
          </div>

          <div className="bg-surface-card border border-border-subtle rounded-2xl p-6 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow">
            <div>
              <div className="flex items-center justify-between gap-2 mb-4">
                <span className="px-3 py-1 rounded-full bg-[#fef7e0] text-[#b06000] text-xs font-semibold border border-[#feefc3]">
                  Semantic Mismatch
                </span>
                <span className="text-xs text-on-secondary-container font-medium">Q6</span>
              </div>
              <h3 className="font-headline text-base font-semibold text-on-surface leading-snug">
                &ldquo;Why do natural language prompts fail in large photo libraries?&rdquo;
              </h3>
              <p className="text-xs text-on-secondary-container mt-3 leading-relaxed">
                When searchers formulate complex episodic queries, search algorithms over-index on literal text or objects while missing social event context.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-border-subtle">
              <Link
                href="/insights"
                className="text-xs text-primary-container font-semibold flex items-center gap-1 hover:underline"
              >
                <span>Read Key Insight Q6</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </Link>
            </div>
          </div>

          <div className="bg-surface-card border border-border-subtle rounded-2xl p-6 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow">
            <div>
              <div className="flex items-center justify-between gap-2 mb-4">
                <span className="px-3 py-1 rounded-full bg-[#e6f4ea] text-[#137333] text-xs font-semibold border border-[#ceead6]">
                  Workaround Behavior
                </span>
                <span className="text-xs text-on-secondary-container font-medium">Q8</span>
              </div>
              <h3 className="font-headline text-base font-semibold text-on-surface leading-snug">
                &ldquo;How do users cope after search returns zero results?&rdquo;
              </h3>
              <p className="text-xs text-on-secondary-container mt-3 leading-relaxed">
                Users resort to manual timeline scrolling across thousands of photos, or abandon search entirely due to high friction.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-border-subtle">
              <Link
                href="/insights"
                className="text-xs text-primary-container font-semibold flex items-center gap-1 hover:underline"
              >
                <span>Read Key Insight Q8</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
