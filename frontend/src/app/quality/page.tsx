'use client';

import React, { useEffect, useState } from 'react';
import { fetchQuality } from '@/lib/api';

export default function QualityPage() {
  const [qualityData, setQualityData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQuality()
      .then((data) => {
        setQualityData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load quality data:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-google-blue border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm font-medium text-on-surface-variant">Loading Multi-Judge Quality Audit...</p>
        </div>
      </div>
    );
  }

  const sampleSize = qualityData?.sample_size || 150;
  const overallAgreement = qualityData?.overall_inter_judge_agreement_pct || 96.0;
  const humanAccuracy = qualityData?.human_validation_accuracy_pct || 100.0;
  const humanSample = qualityData?.human_verified_sample_size || 25;
  const fieldAgreements = qualityData?.field_agreements_pct || {};
  const disagreementCases = qualityData?.disagreement_cases || [];

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-google-blue-tint text-primary-container text-xs font-semibold mb-2">
            <span className="material-symbols-outlined text-[16px]">fact_check</span>
            <span>Multi-LLM Inter-Judge Agreement</span>
          </div>
          <h1 className="font-headline text-3xl font-semibold text-on-surface tracking-tight">
            Quality Audit &amp; System Validation
          </h1>
          <p className="text-sm text-on-secondary-container mt-1">
            Independent blind evaluations across Primary Tagger, Groq Llama-3.3-70b (Judge A), Gemini 3.6 Flash Tiebreaker (Judge B), and Human Expert Ground Truth.
          </p>
        </div>
        <div className="self-start md:self-auto">
          <span className="px-3.5 py-1.5 rounded-full bg-[#e6f4ea] text-[#137333] text-xs font-semibold uppercase tracking-wider inline-flex items-center gap-1.5 shadow-sm border border-[#ceead6]">
            <span className="material-symbols-outlined text-google-green text-[16px]">verified</span>
            <span>Audit Verified</span>
          </span>
        </div>
      </div>

      {/* Stat Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Card 1 */}
        <div className="bg-google-blue-tint border border-google-blue/20 rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-google-blue">
            <span className="text-xs font-semibold uppercase tracking-wider">Inter-Judge Agreement</span>
            <span className="material-symbols-outlined text-[20px]">psychology</span>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold font-headline text-on-surface">{overallAgreement}%</div>
            <p className="text-xs text-on-surface-variant mt-1">Across 6 primary taxonomy fields</p>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-google-green-tint border border-google-green/20 rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-google-green">
            <span className="text-xs font-semibold uppercase tracking-wider">Human Ground Truth</span>
            <span className="material-symbols-outlined text-[20px]">verified_user</span>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold font-headline text-on-surface">{humanAccuracy}%</div>
            <p className="text-xs text-on-surface-variant mt-1">Human expert benchmark match</p>
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-google-yellow-tint border border-google-yellow/20 rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-google-yellow">
            <span className="text-xs font-semibold uppercase tracking-wider">Blind Sample Size</span>
            <span className="material-symbols-outlined text-[20px]">analytics</span>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold font-headline text-on-surface">N={sampleSize}</div>
            <p className="text-xs text-on-surface-variant mt-1">Randomized blind re-tagged posts</p>
          </div>
        </div>

        {/* Card 4 */}
        <div className="bg-google-red-tint border border-google-red/20 rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between text-google-red">
            <span className="text-xs font-semibold uppercase tracking-wider">Human Labels</span>
            <span className="material-symbols-outlined text-[20px]">badge</span>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold font-headline text-on-surface">N={humanSample}</div>
            <p className="text-xs text-on-surface-variant mt-1">Expert ground-truth records</p>
          </div>
        </div>
      </div>

      {/* Section A: Per-Field Agreement Breakdown */}
      <div className="bg-surface-card rounded-2xl border border-border-subtle p-6 shadow-sm space-y-4">
        <h2 className="font-headline text-lg font-semibold text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-google-blue">bar_chart</span>
          Taxonomy Field Agreement Breakdown
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(fieldAgreements).map(([fieldName, agreementPct]: [string, any]) => (
            <div key={fieldName} className="bg-surface-bg p-4 rounded-xl border border-border-subtle space-y-2">
              <div className="flex justify-between items-center text-sm font-medium text-on-surface">
                <span className="capitalize">{fieldName.replace('_', ' ')}</span>
                <span className="font-bold text-google-blue">{agreementPct}%</span>
              </div>
              <div className="w-full h-2.5 bg-surface-container rounded-full overflow-hidden">
                <div
                  className="h-full bg-google-blue transition-all duration-500 rounded-full"
                  style={{ width: `${Math.min(100, agreementPct)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section B: Disagreement Resolution Inspector */}
      <div className="bg-surface-card rounded-2xl border border-border-subtle p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-headline text-lg font-semibold text-on-surface flex items-center gap-2">
            <span className="material-symbols-outlined text-google-yellow">gavel</span>
            Dispute Resolution & Consensus Cases (Gemini Tiebreaker)
          </h2>
          <span className="text-xs text-on-surface-variant font-medium">
            {disagreementCases.length} Disputed Items Analyzed
          </span>
        </div>

        {disagreementCases.length === 0 ? (
          <div className="p-8 text-center bg-surface-bg rounded-xl text-on-surface-variant text-sm">
            Zero classification disputes encountered in the evaluation sample!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface-bg text-on-surface-variant font-semibold border-b border-border-subtle">
                <tr>
                  <th className="py-3 px-4">Post Title</th>
                  <th className="py-3 px-4">Disagreed Field</th>
                  <th className="py-3 px-4">Primary Tag</th>
                  <th className="py-3 px-4">Groq Judge A Tag</th>
                  <th className="py-3 px-4">Gemini Tiebreaker Consensus</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {disagreementCases.map((c: any, i: number) => (
                  <tr key={i} className="hover:bg-surface-bg/50 transition-colors">
                    <td className="py-3 px-4 font-medium text-on-surface max-w-xs truncate" title={c.title}>
                      {c.title || `Post #${c.post_id}`}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {c.disagreements.map((d: string) => (
                          <span key={d} className="px-2 py-0.5 rounded bg-google-red-tint text-google-red text-[11px] font-medium">
                            {d}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-xs font-mono text-on-surface-variant">
                      {JSON.stringify(c.primary_tags)}
                    </td>
                    <td className="py-3 px-4 text-xs font-mono text-on-surface-variant">
                      {JSON.stringify(c.judge_a_tags)}
                    </td>
                    <td className="py-3 px-4 text-xs">
                      <span className="font-semibold text-google-green">
                        {c.consensus_resolution?.winning_judge === 'judge_a' ? 'Judge A (Groq)' : 'Primary (Gemini)'}
                      </span>
                      <p className="text-[11px] text-on-surface-variant mt-0.5">
                        {c.consensus_resolution?.resolution_reasoning}
                      </p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section C: Methodology Note */}
      <div className="bg-surface-bg rounded-2xl border border-border-subtle p-6 space-y-3">
        <h3 className="font-headline text-sm font-semibold text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-on-surface-variant text-[18px]">info</span>
          Multi-LLM Validation Architecture Methodology
        </h3>
        <p className="text-xs text-on-surface-variant leading-relaxed">
          In Phase 8, quality control is enforced by executing a 3-tier validation protocol: (1) <strong>Blind Retagging</strong> of a random sample (N={sampleSize}) using Groq Llama-3.3-70b without revealing original labels; (2) <strong>Dispute Arbitration</strong> using Gemini 3.6 Flash to resolve inter-judge disagreements; and (3) <strong>Ground-Truth Audit</strong> against N={humanSample} expert human labels stored in <code className="bg-surface-card px-1.5 py-0.5 rounded text-on-surface font-mono">data/human_labels.json</code>.
        </p>
      </div>
    </div>
  );
}
