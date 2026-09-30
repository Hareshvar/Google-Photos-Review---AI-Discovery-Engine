# Stitch Design Brief: Retrieval Lens (Google Photos Discovery Engine)

Paste this whole document into Stitch. If it needs to be split, send the "Global design system" section first, then one page section at a time, in the order they appear below.

Output target: **Next.js** (React components, TypeScript, Tailwind CSS if available). If Stitch cannot export Next.js directly, export clean, componentized HTML/CSS with Tailwind classes that map one-to-one onto React components — no inline styles, no single giant page file.

---

## 0. What this product is

"Retrieval Lens" is a research tool, not a consumer app. It shows findings from an AI analysis of public posts (app reviews, Reddit, forums) about people struggling to find old photos in Google Photos when their memory of the photo is incomplete. The audience is a product researcher and reviewers — people reading findings, checking evidence quotes, and asking a chatbot questions. It should feel credible, calm, and evidence-first — not like a marketing dashboard.

---

## 1. Global design system

### 1.1 Visual identity: Google Photos, replicated faithfully

Base the whole visual language on Google Photos and Material 3: clean, light, generous white space, rounded shapes, friendly and calm. **No dark mode.** No gradients, no glassmorphism, no stock photography, nothing that looks like a marketing landing page.

**The four Google Photos colours, each with two shades** (a light "tint" shade for backgrounds/badges, and a solid "base" shade for text, icons, borders, and chart fills):

| Colour | Base shade (solid) | Tint shade (light background) | Meaning in this app |
|---|---|---|---|
| Blue | `#4285F4` (primary actions use `#1A73E8`) | `#E8F0FE` | Information, primary actions, "answered with confidence" |
| Red | `#EA4335` | `#FCE8E6` | Problems, failures, "search broke here" |
| Yellow | `#FBBC04` | `#FEF7E0` | Caution, low confidence, small sample size |
| Green | `#34A853` | `#E6F4EA` | Success, validated, "confirmed by evidence" |

Usage pattern throughout: a badge/chip is the tint shade as background with the base shade as text/border/icon (this is the Material "container" pattern) — never a solid saturated fill covering a large area, and never colour as the *only* signal (always pair with an icon or text label, per accessibility rules below).

**Neutrals:** background `#F8F9FA`, card surface `#FFFFFF`, primary text `#202124`, secondary text `#5F6368`, dividers `#DADCE0`.

**Typography:** Google Sans, falling back to Roboto, falling back to Inter/system sans. Page titles 28-32px semibold. Section titles 20-22px. Body 16px. **Minimum text size anywhere in the app: 14px** — this is a hard floor, not a suggestion.

**Shape:** pill-shaped buttons and search/input fields. 16px corner radius on cards. Subtle shadows only (no heavy drop shadows). Material Symbols Rounded icon set.

### 1.2 Accessibility rules (non-negotiable)

- Never use colour as the only signal for meaning. Every coloured badge/state pairs with an icon and/or a text label (e.g. a red badge also says "Search failed" in text, not just a red dot).
- Text contrast at least 4.5:1 against its background at all times.
- Every chart works for colour-blind readers: use patterns, direct labels on bars/segments, or distinct icons in addition to colour — never rely on a colour legend alone.

### 1.3 Chart and data-display rules (these came from real bugs — follow exactly)

A previous build of this same app had recurring, serious rendering bugs. The design must make these structurally hard to reintroduce:

1. **Every category must have visible room.** If a field being charted has, say, 8 possible values, the chart layout must accommodate all 8 without needing to silently drop, truncate, or scroll past any of them. Design charts (especially cross-tabs/heatmaps) with axis space that can flex/scroll gracefully and legibly, not with a fixed-height list that quietly cuts off entries.
2. **No raw enum codes ever appear on screen.** Every value shown to a user is a short, human-readable phrase (e.g. "Document or receipt," not `document_info`; "Search returned nothing or the wrong results," not `no_or_wrong_results`). Every column header states in plain words what it means (e.g. "% of relevant posts," never a raw variable name like `pct_relevant`).
3. **Axis and column labels never truncate mid-word.** Design for labels to wrap onto two lines or rotate, with enough margin, rather than being cut off with an ellipsis.
4. **Every possible value gets a real label, including "empty"/"not stated."** Never render a bare dash, a literal `None`, or a literal `(empty)` — always a phrase like "Not mentioned in the post."
5. **Distinguish "we checked this and found none" from "we never checked this."** These must look visually different — e.g. a source with zero relevant posts (still collected, just came up empty) should not look identical to a source that was never collected at all.
6. **Long lists always use the collapsible/expandable pattern**, never a long flat scrolling table. A summary row (label + count) that expands on click to reveal detail (quotes, sub-breakdowns) is the default pattern for any list longer than about 6-8 items.

### 1.4 Core reusable components to design

- **StatCard** — a headline number + label, in one of the four tint colours, with a small supporting caption.
- **PipelineStep** — one step in a horizontal step diagram (Collect → Clean → Classify → Analyze → Index → App), each showing a live count, connected by an arrow.
- **ThemeCard** — a named theme/cluster: title, post count, a small bar showing share of total, 2-3 example quote chips, expandable.
- **QuoteCard** — a short quote, its source (Reddit/Play Store/App Store/YouTube/Help Community icon + label), a date, and a "view original" link icon.
- **CollapsibleInsightCard** — collapsed: just the question text + a small chevron. Expanded: LLM-written answer paragraph, one chart, an expandable "See the evidence" row of quote chips. Must support a distinct **"Not enough evidence" state**: a calm, clearly-different visual treatment (yellow tint, an info icon, text like "There isn't enough evidence in the collected data to answer this confidently (n=6). This should be validated through user research.") — not styled like a failed API call or an error state.
- **HeatmapChart** — for two-dimension crosstabs (e.g. photo type × where the search broke). Must show a colour scale legend, full axis labels (wrapped, not truncated), and every category on both axes.
- **BarChart** — single-dimension distributions, always with a value label on or next to each bar (don't make the reader estimate from bar length alone), and an "n=" total shown near the chart title.
- **SituationsTable** — a ranked table with columns: situation (plain-language, e.g. "Document photo · remembered when it was taken · needed it as proof"), post count, share, severity (as a small 3-step indicator, not a raw 1/2/3 number), unresolved rate, opportunity score (a horizontal bar 0-100, described as a score not a percentage). Rows expand to show quotes.
- **ConfidenceChip** — a small tag reading "Low confidence (n<10)" or "Source bias" with a one-line tooltip/caption explaining what that means in plain words, always shown next to any stat it qualifies.
- **ChatMessage / CitationChip** — chat bubble with inline citation markers; clicking a citation highlights the matching entry in a side/bottom evidence panel (source, date, quote, link). Every chatbot answer visually includes up to 3 quote citations, never fewer sourced-but-unlabeled claims.
- **RefusalCard** — a distinct, calm visual state for when the chatbot declines to answer (out of scope, personal data typed in, etc.) — polite tone, states what it can't do and why, and suggests 1-2 things it can answer instead. Should not look like an error.
- **DownloadDashboardButton** — a clearly visible pill button, "Download full analysis," available from the Overview page and ideally as a persistent element (e.g. in the top bar), for exporting the complete findings bundle.
- **ExpandableEvidenceRow** — the shared "click to see 2-3 supporting quotes" pattern used across Themes, Situations, and Key Insights, so it looks and behaves identically everywhere it appears.

### 1.5 Layout shell

- **Top bar:** small four-petal "pinwheel" logo mark (in the four brand colours) + "Retrieval Lens" wordmark, a "Download full analysis" button, and a small "Demo data" badge (shown only when applicable — see 1.6).
- **Left navigation rail** (Google Photos style): Overview, Themes, Situations, Key Insights, Ask the data, Method and limits. A "Quality check" item appears in the nav **only if the optional LLM-judge/human-validation stage has been run** — otherwise it's simply absent, not shown greyed-out.
- Responsive: a clean single-column layout with a bottom nav or hamburger drawer on mobile (390px width), the two-column layout (nav rail + content) from 1024px up.

### 1.6 Demo-data state

Whenever the underlying data is a placeholder/demo dataset rather than real collected data, a persistent, unmissable yellow-tint banner appears at the top of every page: "Demo data — for layout preview only." This is a real functional state the components must support, not just a note for this brief.

---

## 2. Page: Overview

- Header: "Why can't people find the photo they remember?" + one-line explanation.
- Four StatCards (one per brand colour): Posts collected (blue), Classified as relevant (green), Vague-memory posts (yellow), Search failures (red) — real counts, not samples.
- The **pipeline step diagram** (PipelineStep components, section 1.4), reading left to right, each with a live count. Include the conditional "Checked (LLM judges + human sample)" step only when that stage has run.
- A **source health row**: one chip per source (Reddit r/googlephotos, Reddit r/GeminiAI, Play Store, App Store, YouTube, Help Community), each showing rows collected and "X% relevant" — and visually distinguishing a source that yielded zero relevant posts from one that was never collected (see 1.3, rule 5).
- A short list of "Questions this data can help answer" (linking down to Key Insights).
- Primary button: "Explore themes." Secondary button: "Ask the data."

## 3. Page: Themes

Two clearly, separately titled sections on one page — do not merge them into a single chart, since they answer different questions.

- **Section A — "Where do people struggle"**: a HeatmapChart of failure step × system issue, ranked by count. Full axis labels, legend, every category visible.
- **Section B — "What people are discussing"**: a ranked list of ThemeCards (named clusters, e.g. "Search regressed after an update," "Face/person search broken," "Text-in-photo search degraded"), each with count, share, and 2-3 quote chips.
- Below both sections, a small, clearly separate, non-ranked disclosure line: "X% of posts (n) did not fit a named theme." This must **never** appear as a bar inside either chart above — it is always outside the ranked visuals, styled as a neutral footnote, not a competing result.

## 4. Page: Situations

- One SituationsTable, sorted by opportunity score by default (with a visible control to re-sort by count or severity).
- A small caption explaining the opportunity score formula in plain words.
- A note: "These are situations, not user demographics — public posts don't reveal age, location, or occupation."
- A single "Other (fewer than 10 posts)" row at the bottom, visually de-emphasized but still shown (this is a transparent small-sample disclosure, not hidden).

## 5. Page: Key Insights

- Section header explaining this page collapses each research question and expands it into an evidence-backed answer.
- Nine CollapsibleInsightCards (What kinds of photos are hard to find; What people remember; What people forget; How they search when memory is incomplete; Whether they can express what they remember; Whether Photos understands their clues; Whether results are hard to evaluate; Whether they struggle to refine a search; Where in the retrieval journey the major breaks happen).
- Each must support both states: a normal evidence-backed answer, and the "not enough evidence" state (see 1.4).

## 6. Page: Ask the data

- Welcome message + 3 example question chips (e.g. "What do people forget about a photo?", "Which photo types fail most?", "Where does search break down most?").
- Persistent disclaimer text: "Answers come only from the public posts we collected. Not a measure of all Google Photos users."
- Chat area with ChatMessage bubbles; every assistant answer shows up to 3 CitationChips inline, and clicking one opens/highlights the matching entry in a side panel (bottom sheet on mobile) with the full quote, source, date, and a link.
- A visible "questions remaining this session" counter.
- A RefusalCard state, styled distinctly (calm, not error-red), for out-of-scope questions or personal-data attempts.
- An empty/no-evidence state: "Not enough evidence in the collected posts for that question," with a suggestion of 1-2 answerable alternatives.

## 7. Page: Method and limits

- The same pipeline diagram as Overview, but each step is expandable to show exact counts dropped/kept at that stage.
- A source table: rows collected, % relevant, any known limitation per source (e.g. "App Store: platform limits us to the most recent ~500 reviews per country").
- Model/version info: tagging model, prompt version, taxonomy version (small, technical, low visual priority — a simple table is fine here, this section can be plainer than the rest of the app).
- A plain-language "What this data can and can't tell you" list.
- A glossary: every tag field and value used elsewhere in the app, defined in one line each.

## 8. Page: Quality check (conditional — only exists if the LLM-judge/human stage has run)

- A summary card: how many posts were double-checked, agreement rate between the tagging model, the two LLM judges, and the human labels, shown as a simple comparison (not a dense confusion matrix as the primary visual — keep this page readable for a non-technical reviewer, with a "see full detail" expandable section for the complete numbers).
- Plain-language framing throughout: "the human check is the most trustworthy, but only covers a small sample — treat this as directional, not final."

---

## 9. What NOT to do

- Do not invent sample data with unrealistic round numbers (e.g. exactly 50/50 splits) — use plausible, slightly uneven placeholder numbers so the layout is tested against realistic variation (long labels, small counts, uneven bar lengths).
- Do not add features not listed here (no user accounts, no settings page, no notifications).
- Do not use a dark background anywhere, even for the chat page.
- Do not represent the KPI tree as a diagram anywhere in this app — failure-step data is shown only as charts (Themes Section A, Key Insights Q9), never as a tree/flowchart visual.
