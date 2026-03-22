# IGSHIELD UI Enhancement (React) — Cursor Implementation Spec

Goal: Upgrade the IGSHIELD UI to look **sophisticated, professional, and user-friendly**, with **Event Logs hidden by default** behind a **Developer Mode** toggle. Replace the always-visible log panel with a **Results** panel and add a **Developer Drawer** for logs.

This spec assumes:
- Frontend: React + TypeScript
- Styling: Tailwind CSS
- UI kit: shadcn/ui (recommended)
- Icons: lucide-react
- Optional animation: framer-motion (subtle only)

---

## 0) High-level UX changes (non-negotiables)

### A. Layout becomes “Setup → Run → Results”
Replace the existing 3-column (Inputs / Pipeline / Logs) with:

1) **Left panel: Setup**
   - PDF Upload
   - Answer key upload (optional)
   - Attack methods selection (card-based, not small checkboxes)
   - Compilation toggle
   - Primary CTA: Run Pipeline
   - Secondary: Reset

2) **Center panel: Pipeline Timeline**
   - Vertical timeline with step numbers (1–6)
   - Status pills per step (Queued / Running / Done / Failed)
   - Progress (e.g., 12/30) where available
   - Clicking a step opens a **Step Details drawer** (right side or bottom)

3) **Right panel: Results (default)**
   - Run Summary (counts, runtime, selected attack methods)
   - Evaluation highlights (if available)
   - Artifacts grouped by stage with download/preview actions

### B. Logs are hidden by default
- Add a **Developer Mode toggle** in the TopBar (top-right).
- When Developer Mode is ON:
  - Show a “Developer” button.
  - Clicking it opens a **Developer Drawer** with logs + trace JSON + copy actions.
- When Developer Mode is OFF:
  - No logs UI visible.
  - Only friendly status updates are shown (non-technical).

---

## 1) Visual style principles (make it look “premium”)

### Typography & spacing
- Use a consistent spacing scale (Tailwind defaults ok).
- Headers: slightly larger, strong contrast.
- Secondary text: lower opacity but readable.
- Avoid heavy outlines; prefer soft shadows and subtle borders.

### Colors & states
- Use *one* accent color (existing teal/green is fine).
- Status colors:
  - Running: blue-ish
  - Done: green
  - Failed: red
  - Queued: neutral/gray
- Keep backgrounds dark but improve contrast on text.

### Interaction polish
- Subtle hover states for cards and list items.
- Skeleton loading for artifacts while waiting.
- Toast notifications for major events (start, stage complete, run finished).

---

## 2) Component plan (what to build)

### 2.1 App shell
**`AppShell`**
- Provides overall layout and background.
- Uses a 12-col grid:
  - Left: 3 cols
  - Center: 5 cols
  - Right: 4 cols
- Responsive: on smaller screens collapse into tabs or stacked sections.

**`TopBar`**
- Left: IGSHIELD + subtitle (“Document Integrity Pipeline”)
- Right:
  - Run state pill: Idle / Running / Done / Failed
  - Developer Mode toggle (switch)
  - If devMode ON: “Developer” button opens drawer

### 2.2 Setup panel (left)
**`SetupPanel`**
- `UploadCard` for PDF (required)
- `UploadCard` for Answer Key (optional) + helper text: “Improves evaluation scoring”
- `AttackMethodPicker`:
  - Replace checkboxes with selectable cards
  - Each card: title, 1-line description, tooltip “Learn more”
  - Supports multi-select
  - One card can be tagged “Recommended”
- `CompileToggle`:
  - Label: “Compile attacked PDFs”
  - Helper text: “If off, only .tex is generated”
- Run controls:
  - Primary button: Run Pipeline
  - Disabled until PDF present
  - Show inline validation (“Upload a PDF to continue”)
  - Secondary: Reset

### 2.3 Pipeline timeline (center)
**`PipelineTimeline`**
- Steps in fixed order:
  1. PDF Ingestion
  2. Document Extraction
  3. Perturbation Planning
  4. Attack Injection
  5. Compilation
  6. Evaluation
- Each step shows:
  - Step number + title
  - Status pill
  - Short summary line (human readable)
  - Progress text when available (“12/30”, “10 questions”)
  - Duration when done (“7.2s”)
- Clicking a step opens **`StepDetailsDrawer`**
  - Shows: outputs, warnings, key metrics
  - If devMode ON: show raw JSON for the step

### 2.4 Results panel (right)
**`ResultsPanel`**
- `RunSummaryCard`
  - Extracted questions count
  - Perturbations generated
  - Methods selected
  - Compilation enabled/disabled
  - Total runtime
- `EvaluationHighlightsCard` (optional when data exists)
  - ASR / Task Degradation / Tool Misfire / Resource Inflation (only show what you have)
- `ArtifactsList`
  - Grouped by stage
  - Each artifact row:
    - file icon
    - name
    - type badge (PDF/TEX/JSON/ZIP)
    - actions: Preview (if PDF), Download, Copy link

### 2.5 Developer drawer (logs)
**`DeveloperDrawer`**
- Only accessible when devMode ON.
- Slide-over drawer from right.
- Tabs:
  - Logs
  - Trace JSON
  - Tool Calls (optional)
- Logs have:
  - filter by level (INFO/WARN/ERROR)
  - search
  - Copy logs button
- IMPORTANT: logs should NOT take space in the main layout.

### 2.6 Friendly status feed (replaces logs for normal users)
**`StatusFeed`** (small, non-technical)
- Appears in ResultsPanel near top or inside RunSummary
- Shows last ~5 pipeline messages:
  - “PDF uploaded”
  - “Extracted 10 questions”
  - “Generated 30 perturbations”
- No raw JSON, no stack traces.

---

## 3) Data/state model (front-end contract)

Create a single run state object, something like:

```ts
export type StepId = "ingest" | "extract" | "plan" | "inject" | "compile" | "eval";

export type StepStatus = "queued" | "running" | "done" | "failed";

export type RunStatus = "idle" | "running" | "done" | "failed";

export type RunState = {
  runId?: string;
  status: RunStatus;
  devMode: boolean;

  config: {
    attacks: string[];
    compile: boolean;
    answerKeyProvided: boolean;
  };

  steps: Array<{
    id: StepId;
    title: string;
    status: StepStatus;
    summary?: string;
    progress?: { current: number; total: number };
    durationSec?: number;
    outputs?: Array<{ label: string; value: string }>;
    warnings?: string[];
    raw?: unknown; // show only in dev mode
  }>;

  artifacts: Array<{
    stageId: StepId;
    name: string;
    type: "pdf" | "tex" | "json" | "zip";
    sizeKB?: number;
    url?: string;
  }>;

  statusFeed: Array<{ ts: string; msg: string }>;

  logs?: Array<{ ts: string; level: string; msg: string; meta?: unknown }>;
};

4) Real-time updates (SSE/WS) — required behavior
Implement useRunStream(runId) to subscribe to backend events.
Minimum event types to support:
RUN_STARTED
STEP_STARTED
STEP_PROGRESS
STEP_COMPLETED
STEP_FAILED
ARTIFACT_CREATED
RUN_COMPLETED
LOG_LINE (devMode only shows, but still collect)
Front-end logic:
Always append human-readable messages to statusFeed (last 5–10).
Store logs regardless, but render only when devMode ON.
On failure:
show a user-friendly error banner with “Retry” and (if devMode ON) “Show details”.
5) Implementation tasks (Cursor TODO list)
Task 1 — Create new layout + panels
Create AppShell, TopBar, SetupPanel, PipelineTimeline, ResultsPanel.
Replace existing Event Log column with ResultsPanel.
Acceptance:
UI looks balanced and professional.
No logs visible in the main layout.
Task 2 — Developer Mode toggle + Developer Drawer
Add toggle in TopBar controlling devMode.
When devMode ON:
show “Developer” button
open DeveloperDrawer with logs and copy button
Acceptance:
Logs are only visible inside the drawer.
Drawer does not affect main layout width when closed.
Task 3 — Attack method selector redesign
Replace checkbox list with card-based multi-select.
Add tooltips and “Recommended” badge.
Acceptance:
Selector is intuitive and visually clean.
Task 4 — Pipeline timeline polish + step details drawer
Add step numbers and status pills.
Add click-to-open drawer showing step outputs/warnings.
In devMode show raw JSON.
Acceptance:
Timeline feels like an orchestration UI, not a list of cards.
Task 5 — Results panel and artifacts grouping
Add Run Summary card
Add Evaluation highlights (optional)
Artifacts grouped by stage with actions
Acceptance:
Users can quickly understand “what happened” and “what to download.”
Task 6 — Real-time event wiring
Implement useRunStream to update run state.
Add skeletons/spinners where appropriate.
Add toast notifications for stage completions.
Acceptance:
UI updates smoothly during a live run.
6) Folder structure (recommended)
src/
  components/
    shell/
      AppShell.tsx
      TopBar.tsx
    setup/
      SetupPanel.tsx
      UploadCard.tsx
      AttackMethodPicker.tsx
      CompileToggle.tsx
    pipeline/
      PipelineTimeline.tsx
      StepCard.tsx
      StepDetailsDrawer.tsx
    results/
      ResultsPanel.tsx
      RunSummaryCard.tsx
      EvaluationHighlightsCard.tsx
      ArtifactsList.tsx
      ArtifactRow.tsx
      StatusFeed.tsx
    dev/
      DeveloperDrawer.tsx
      LogsViewer.tsx
      TraceViewer.tsx
  hooks/
    useRunStream.ts
  lib/
    types.ts
    api.ts
    utils.ts
  pages/
    Dashboard.tsx
7) UI details to match “sophisticated/professional” (do these)
Reduce noisy borders; use subtle separators and shadowed panels.
Make buttons consistent: primary filled, secondary ghost/outline.
Make cards consistent: same padding, radius, and header style.
Add “Empty states”:
No artifacts yet
No evaluation yet
Add accessibility:
visible focus ring
good contrast
keyboard navigation for drawer
8) Final acceptance checklist
 Logs are hidden by default and only appear in Developer Drawer.
 Setup → Timeline → Results layout is implemented.
 Attack methods are card-based and user-friendly.
 Pipeline steps have clear statuses and progress.
 Clicking steps reveals details (drawer).
 Results panel shows summary + artifacts grouped by stage.
 UI looks cohesive (consistent spacing/typography).
 Works during live runs (SSE/WS), with good loading states.
9) Notes for Cursor
Use shadcn/ui components: Card, Button, Badge, Tabs, Sheet/Drawer, Switch, Tooltip, Separator, ScrollArea.
Use lucide icons for file types and statuses.
Keep animations minimal (subtle transitions only).
Avoid overcomplication: prioritize clean hierarchy and clarity.