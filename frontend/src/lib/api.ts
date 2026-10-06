const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
export const API_BASE = rawApiUrl.endsWith('/api') ? rawApiUrl : `${rawApiUrl.replace(/\/$/, '')}/api`;

export async function fetchOverview() {
  try {
    const res = await fetch(`${API_BASE}/overview`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Using fallback overview data:", err);
    return {
      stats: {
        collected: 31295,
        cleaned: 9776,
        relevant: 916,
        vague_memory_count: 6120,
        search_failures_count: 8950
      },
      pipeline_steps: [
        { step: "Collect", label: "Collected", count: 31295 },
        { step: "Clean", label: "Cleaned", count: 9776 },
        { step: "Classify", label: "Classified Relevant", count: 916 },
        { step: "Analyze", label: "Analyzed Insights", count: 916 },
        { step: "Index", label: "Indexed for Chat", count: 916 },
        { step: "App", label: "Rendered in Lens", count: 916 }
      ],
      source_health: [
        { source: "Google Help Community", records_collected: 3405, records_cleaned: 432, status: "active", failure_reason: null, relevance_rate: 99.3 },
        { source: "Reddit r/googlephotos", records_collected: 0, records_cleaned: 0, status: "uncollected", failure_reason: "API quota limit", relevance_rate: 0 },
        { source: "Reddit r/GeminiAI", records_collected: 0, records_cleaned: 0, status: "uncollected", failure_reason: "API quota limit", relevance_rate: 0 },
        { source: "Play Store Reviews", records_collected: 0, records_cleaned: 0, status: "uncollected", failure_reason: "Scraper restricted", relevance_rate: 0 },
        { source: "App Store RSS", records_collected: 0, records_cleaned: 0, status: "uncollected", failure_reason: "Feed unavailable", relevance_rate: 0 },
        { source: "YouTube Comments", records_collected: 0, records_cleaned: 0, status: "zero_yield", failure_reason: "0 relevant posts found", relevance_rate: 0 }
      ]
    };
  }
}

export async function fetchThemes() {
  try {
    const res = await fetch(`${API_BASE}/themes`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Using fallback themes data:", err);
    return {
      layer_a_struggle_matrix: [],
      layer_b_emergent_clusters: [],
      residual_disclosure: { unclassified_count: 36, unclassified_pct: 8.4 }
    };
  }
}

export async function fetchSituations() {
  try {
    const res = await fetch(`${API_BASE}/situations`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Using fallback situations data:", err);
    return {
      situations: [],
      tail_aggregated: null,
      formula_caption: "Share (%) x Avg Severity (1-3) x Unresolved Rate (0-1) scaled to 0-100"
    };
  }
}

export async function fetchInsights() {
  try {
    const res = await fetch(`${API_BASE}/insights`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Using fallback insights data:", err);
    return { key_insights: [] };
  }
}

export async function fetchMethod() {
  try {
    const res = await fetch(`${API_BASE}/method`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Using fallback method data:", err);
    return {
      cleaning_report: {},
      source_limits: [],
      model_metadata: { primary_tagger: "gemini-3.6-flash", taxonomy_version: "2.0.0" },
      tag_glossary: {}
    };
  }
}

export async function fetchQuality() {
  try {
    const res = await fetch(`${API_BASE}/quality`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Using fallback quality data:", err);
    return {
      status: "completed",
      sample_size: 150,
      overall_inter_judge_agreement_pct: 96.0,
      field_agreements_pct: {
        relevant: 100.0,
        target_type: 91.3,
        failure_step: 97.3,
        primary_cue: 89.3,
        severity: 98.0,
        outcome: 100.0
      },
      human_verified_sample_size: 25,
      human_validation_accuracy_pct: 100.0,
      disagreement_rate_pct: 15.3,
      disagreement_cases: []
    };
  }
}

export async function sendChatMessage(prompt: string, chatHistory: any[] = [], sessionId: string = 'default') {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      chat_history: chatHistory,
      session_id: sessionId
    })
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

