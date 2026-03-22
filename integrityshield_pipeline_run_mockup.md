# IntegrityShield Pipeline Run Mockup

## Goal
Redesign the **Pipeline Run** tab so it feels active, informative, and polished instead of sparse and static.

The screen should communicate that the system is executing a structured multi-stage document protection workflow.

---

## Core Design Direction
Replace the current plain vertical text list with a **large interactive stage-card layout**.

Each stage should:
- have an icon
- have a title
- have a 1-line summary
- show a clear status badge
- be clickable / expandable
- reveal a high-level overview when expanded

This makes the page feel like a real pipeline visualizer rather than a placeholder list.

---

## Recommended Top-Level Structure

```text
┌────────────────────────────────────────────────────────────────────┐
│ Pipeline Run                                                      │
│ Track each stage from ingestion to evaluation                     │
│                                                                    │
│ [ Overall Progress Bar / Pipeline Flow Strip ]                    │
│                                                                    │
│ [ Active Run Summary Card ]                                       │
│                                                                    │
│ [ Stage Card Grid ]                                               │
│   [PDF Ingestion]     [Document Extraction]                       │
│   [Planning]          [Shield Injection]                          │
│   [Compilation]       [Evaluation]                                │
│                                                                    │
│ [ Expanded Stage Details Drawer / Panel ]                         │
└────────────────────────────────────────────────────────────────────┘
```

---

## 1. Add a Pipeline Flow Strip at the Top
At the top of the page, add a visual flow strip showing the 6 stages in order.

### Example
```text
📄 Ingestion → 🔍 Extraction → 🧠 Planning → 🛡 Injection → 📦 Compilation → 📊 Evaluation
```

### Behavior
- highlight the current stage
- completed stages get a green check state
- running stage gets blue highlight / pulse
- queued stages remain muted

This gives immediate context and uses the horizontal space effectively.

---

## 2. Add an Overall Run Summary Card
Directly below the flow strip, add a compact summary card.

### Example contents
- Run status: `Queued`, `Running`, `Completed`, `Failed`
- Selected shielding method
- Uploaded assessment filename
- Started time
- Current stage

### Example copy
**Run Summary**  
Method: Dual Layer  
Status: Running  
Current Stage: Perturbation Planning  
Assessment: midterm_exam.pdf

This makes the top part feel alive and informative.

---

## 3. Replace the Text List with Large Stage Cards
Instead of a numbered list, use **2-column stage cards**.

### Recommended grid
```text
[📄 PDF Ingestion]         [🔍 Document Extraction]
[🧠 Perturbation Planning] [🛡 Shield Injection]
[📦 PDF Compilation]       [📊 Evaluation]
```

### Why this is better
- uses empty space effectively
- feels more visual and modern
- easier to scan
- gives each stage more presence
- supports click-to-inspect naturally

---

## 4. Recommended Stage Card Content
Each card should show:
- icon
- stage name
- 1-line description
- status badge
- optional mini metadata like elapsed time or output summary
- chevron icon indicating expandability

### Example card
```text
┌──────────────────────────────────────┐
│ 🧠 Perturbation Planning        Running│
│ Generate the shielding plan based on │
│ the selected method and document.    │
│                                      │
│ View stage overview            ▾     │
└──────────────────────────────────────┘
```

---

## 5. Suggested Icons Per Stage
Use clean outline icons.

- **PDF Ingestion** → file/document icon
- **Document Extraction** → search / scan icon
- **Perturbation Planning** → brain / sparkles / workflow icon
- **Shield Injection** → shield icon
- **PDF Compilation** → package / layers / file stack icon
- **Evaluation** → chart / bar graph / check-circle icon

If using Lucide icons, good options include:
- `FileText`
- `ScanSearch`
- `BrainCircuit`
- `ShieldCheck`
- `Package`
- `BarChart3`

---

## 6. Add Status Badges with Strong Visual Identity
Status should not just be text. Use badges.

### Recommended badge styles
- **Queued** → muted gray badge
- **Running** → blue badge with animated pulse dot
- **Completed** → green badge with check icon
- **Failed** → red badge with alert icon

### Example
```text
[Queued]
[Running ●]
[Completed ✓]
[Failed !]
```

This instantly improves scannability.

---

## 7. Make Cards Expandable (Important)
Yes, you should absolutely implement click-to-inspect.

### Interaction
When the user clicks a stage card:
- expand the card inline, or
- open a side panel / bottom drawer with high-level details

### Keep details high-level
Do not dump raw logs by default.

Show things like:
- what the stage does
- what input it receives
- what output it produces
- current status
- short summary of what happened

### Example expanded content
**Perturbation Planning**  
This stage analyzes the extracted document structure and selected shielding method to generate a protection plan.

**Inputs**
- extracted document structure
- selected shielding method

**Outputs**
- perturbation blueprint
- placement plan

**Current state**
Queued — waiting for extraction to complete.

---

## 8. Example High-Level Details for Each Stage

### PDF Ingestion
- validates uploaded file
- checks file availability
- prepares it for downstream parsing

### Document Extraction
- extracts text blocks, layout structure, pages, and metadata
- prepares internal representation of the assessment

### Perturbation Planning
- selects and plans the shielding transformations
- decides where and how to apply them

### Shield Injection
- applies chosen perturbations into the document layers / content
- generates shielded intermediate output

### PDF Compilation
- compiles the modified artifacts into the final shielded PDF
- verifies export success

### Evaluation
- runs detection / protection checks
- prepares the final report and metrics

---

## 9. Suggested Layout for Expanded Details
There are 3 good options.

### Option A — Expand within the card
Best for compact context.

### Option B — Right-side detail panel
Best if you want a polished app-like feel.

### Option C — Bottom inspector drawer
Best if you want to keep the grid visible above.

### Best recommendation for IntegrityShield
Use a **right-side inspector panel on desktop**.

Layout example:
```text
[ Stage Card Grid ]     [ Selected Stage Details ]
```

This makes the screen feel much more premium.

---

## 10. Better Use of Screen Space
Right now there is too much dead space because the content is a narrow text stack inside a large container.

### Fixes
- use a grid instead of a list
- increase card height
- add more visual hierarchy at top
- optionally split the page into:
  - left = stage grid
  - right = inspector panel

### Recommended desktop layout
```text
┌──────────────────────────────┬──────────────────────────────┐
│ Stage Grid                   │ Stage Inspector              │
│                              │                              │
│ [Ingestion] [Extraction]     │ Selected Stage: Extraction   │
│ [Planning ] [Injection ]     │ Summary / Inputs / Outputs   │
│ [Compile  ] [Evaluation]     │ Status / Overview            │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 11. Add Motion / Micro-Interactions
Use subtle animations so the page feels alive.

### Recommended
- card hover lift
- animated border or glow on active stage
- smooth expand/collapse transition
- pulse dot on running stage
- progress strip animation
- success check animation on completion

Keep it minimal and professional.

---

## 12. Improve the Empty / Pre-Run State
Current message:
> Start a run from Main to begin.

This is too bare.

### Better pre-run state
Show a centered informative empty state card:

**No active pipeline run**  
Start the shielding workflow from the Main tab to process the uploaded assessment and generate results.

Add a subtle icon and optionally a button:
- `Go to Main`

---

## 13. Example Visual Structure for the Final Page

```text
┌────────────────────────────────────────────────────────────────────┐
│ Pipeline Run                                                      │
│ Track each stage from ingestion to evaluation                     │
│                                                                    │
│ 📄 Ingestion → 🔍 Extraction → 🧠 Planning → 🛡 Injection → 📦 Compile → 📊 Evaluate │
│                                                                    │
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │ Run Summary                                                  │   │
│ │ Method: Dual Layer   Status: Running   Current: Planning     │   │
│ └──────────────────────────────────────────────────────────────┘   │
│                                                                    │
│ ┌────────────────────────────┬──────────────────────────────────┐  │
│ │ 🧠 Planning                │ Selected Stage Details           │  │
│ │ Running                    │                                  │  │
│ │ Generate shielding plan    │ Perturbation Planning            │  │
│ ├────────────────────────────┤ Generates the plan for applying  │  │
│ │ 🛡 Injection               │ document-layer shielding.        │  │
│ │ Queued                     │                                  │  │
│ ├────────────────────────────┤ Inputs / Outputs / Summary       │  │
│ │ 📦 Compilation             │                                  │  │
│ │ Queued                     │                                  │  │
│ └────────────────────────────┴──────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 14. Recommended Component Structure

### Components
- `PipelineRunPage`
- `PipelineFlowStrip`
- `RunSummaryCard`
- `StageGrid`
- `PipelineStageCard`
- `StatusBadge`
- `StageInspectorPanel`
- `EmptyRunState`

### Suggested props for stage cards
- `title`
- `icon`
- `description`
- `status`
- `isActive`
- `onClick`

### Suggested props for inspector
- `selectedStage`
- `details`
- `developerMode`

---

## 15. Developer Mode Integration
When `Developer Mode` is ON, the inspector panel can reveal an extra diagnostics section.

### Additional details in developer mode
- runtime duration
- timestamps
- file counts
- extracted block count
- perturbation count
- evaluation metrics
- raw stage notes

When OFF, keep the inspector high-level and clean.

---

## 16. Cursor Implementation Brief
Implement the Pipeline Run tab as a **2-column, card-based interactive pipeline dashboard**.

### Requirements
- top pipeline progress strip with icons and stage highlighting
- compact run summary card below
- 2-column grid of large stage cards
- each stage card clickable
- selected stage opens high-level inspector panel on the right
- visual status badges for queued/running/completed/failed
- subtle Framer Motion transitions
- dark theme aligned with IntegrityShield branding
- optional developer diagnostics within inspector when Developer Mode is enabled

---

## 17. One-Sentence Design Brief
Redesign the Pipeline Run tab into a visually rich, interactive stage dashboard with large icon-based cards, clear status indicators, and a side inspector panel so users can understand both pipeline progress and high-level stage behavior at a glance.

