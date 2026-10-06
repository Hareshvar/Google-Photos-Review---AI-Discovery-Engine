import React from 'react';

export interface MatrixCell {
  failure_step: string;
  system_issue: string;
  count: number;
  share_pct?: number;
  pct?: number;
}

interface HeatmapChartProps {
  matrix: MatrixCell[];
  totalRelevant?: number;
}

const HUMAN_FAILURE_STEPS: Record<string, string> = {
  did_not_search: 'Did Not Search',
  search_not_completed: 'Search Not Completed',
  no_or_wrong_results: 'No or Wrong Results',
  results_not_recognized: 'Results Not Recognized',
  wrong_photo_opened: 'Wrong Photo Opened',
  scroll_not_found: 'Scroll / Timeline Search Failed',
  no_failure: 'No Failure (Found)',
  unclear: 'Unclear / Other'
};

const HUMAN_SYSTEM_ISSUES: Record<string, string> = {
  missing_results: 'Missing / No Results',
  face_rec_failure: 'Face Recognition Failure',
  date_index_error: 'Date / Timeline Indexing Error',
  ocr_failure: 'OCR / Text Search Failure',
  ui_regression: 'UI / Layout Regression',
  ask_photos_hallucination: 'Ask Photos Hallucination',
  wrong_results: 'Incorrect / Irrelevant Results',
  ocr_text_failed: 'OCR / Text Failed',
  face_detection_broken: 'Face Detection Broken',
  semantic_mismatch: 'Semantic Mismatch',
  date_metadata_lost: 'Date Metadata Lost',
  location_missing: 'Location Missing',
  none_app_worked: 'None (App Worked)',
  unclear_other: 'Unclear / Other'
};

export const HeatmapChart: React.FC<HeatmapChartProps> = ({
  matrix,
  totalRelevant = 916,
}) => {
  // Extract unique failure steps and system issues present in data
  const failureSteps = Array.from(new Set(matrix.map((m) => m.failure_step)));
  const systemIssues = Array.from(new Set(matrix.map((m) => m.system_issue)));

  // Lookup map: `${failure_step}:${system_issue}` -> cell
  const cellMap = new Map<string, MatrixCell>();
  matrix.forEach((m) => {
    cellMap.set(`${m.failure_step}:${m.system_issue}`, m);
  });

  // Calculate max count for color intensity scale
  const maxCount = Math.max(...matrix.map((m) => m.count), 1);

  const getIntensityClass = (count: number) => {
    if (count === 0) return 'bg-surface-bg text-on-secondary-container';
    const ratio = count / maxCount;
    if (ratio > 0.6) return 'bg-google-red text-white font-bold';
    if (ratio > 0.3) return 'bg-google-red-tint text-google-red font-semibold';
    return 'bg-surface-container text-on-surface';
  };

  return (
    <div className="bg-surface-card border border-border-subtle rounded-2xl p-6 shadow-sm overflow-hidden flex flex-col gap-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-border-subtle pb-4">
        <div>
          <h3 className="font-headline text-lg font-semibold text-on-surface">
            Section A — Search Failure Step vs System Issue Matrix
          </h3>
          <p className="text-xs text-on-secondary-container mt-0.5">
            Cross-tabulation of failure breakdown stages against underlying system flaws (% of N={totalRelevant.toLocaleString()} relevant posts)
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-xs text-on-secondary-container">
          <span className="font-semibold">Intensity:</span>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-surface-bg border border-border-subtle" /> Low
            <span className="w-3 h-3 rounded bg-google-red-tint ml-1" /> Med
            <span className="w-3 h-3 rounded bg-google-red ml-1" /> High
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="overflow-x-auto">
        <table className="w-full text-center border-collapse">
          <thead>
            <tr>
              <th className="p-3 text-left text-xs font-semibold text-on-surface-variant bg-surface-bg border-b border-r border-border-subtle min-w-[200px]">
                Failure Step \ System Issue
              </th>
              {systemIssues.map((sys, idx) => (
                <th
                  key={idx}
                  className="p-3 text-xs font-semibold text-on-surface bg-surface-bg border-b border-border-subtle min-w-[130px] leading-tight"
                >
                  {HUMAN_SYSTEM_ISSUES[sys] || sys}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {failureSteps.map((fs, fsIdx) => (
              <tr key={fsIdx}>
                <td className="p-3 text-left font-semibold text-xs text-on-surface bg-surface-bg border-r border-border-subtle">
                  {HUMAN_FAILURE_STEPS[fs] || fs}
                </td>
                {systemIssues.map((sys, sysIdx) => {
                  const cell = cellMap.get(`${fs}:${sys}`) || {
                    failure_step: fs,
                    system_issue: sys,
                    count: 0,
                    share_pct: 0,
                    pct: 0,
                  };
                  const pctVal = cell.share_pct ?? cell.pct ?? (totalRelevant > 0 ? ((cell.count / totalRelevant) * 100) : 0);
                  return (
                    <td
                      key={sysIdx}
                      className={`p-3 transition-colors ${getIntensityClass(
                        cell.count
                      )} border-r last:border-r-0 border-border-subtle/30`}
                    >
                      <div className="text-sm font-semibold">{cell.count.toLocaleString()}</div>
                      <div className="text-[11px] opacity-90">{pctVal.toFixed(1)}%</div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
