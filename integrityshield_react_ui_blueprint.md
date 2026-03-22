# IntegrityShield React UI Redesign Blueprint

## Goal
Redesign the IntegrityShield interface from a developer-centric dashboard into a polished, guided workflow that feels professional, modern, and easy for non-technical users to navigate.

The UI should communicate that IntegrityShield is a **document protection and assessment shielding system**, not just a pipeline debugger.

---

## Product Positioning
The interface should visually communicate:
- academic integrity
- document protection
- safe, controlled AI workflow
- research-grade sophistication
- ease of use for instructors / evaluators / researchers

Avoid exposing too much low-level system information on the main screen.

The UI should feel closer to:
- a premium AI product
- a secure document workflow platform
- a guided multi-step application

Not like:
- a raw internal admin panel
- a debugging console
- a logs-heavy engineering tool

---

## Core UX Direction
The application should follow a clean **4-step guided workflow**:

1. **Upload**
2. **Configure Shielding**
3. **Run Pipeline**
4. **View Results**

Users should not see all technical sections at once.
Use **progressive disclosure** so that each section appears when needed.

Example flow:

- User uploads assessment and optional answer key
- Assessment preview appears
- Shielding methods section expands
- User selects one shielding method
- Run button becomes active
- Pipeline progress is shown in a dedicated tab
- Final results appear in the results tab

---

## Header / Navigation
Create a clean top navigation bar with the IntegrityShield brand on the left and product navigation in the center.

### Header tabs
Use these three tabs:
- **Main**
- **Pipeline Run**
- **Results**

### Right side of header
Place:
- system status indicator (`Idle`, `Running`, `Completed`, `Error`)
- `Developer Mode` toggle

### Behavior
- By default, `Developer Mode` is OFF
- When OFF, hide logs, timestamps, raw stage metadata, evaluation internals, and engineering diagnostics
- When ON, reveal a developer panel or expanded technical details in the Pipeline Run and Results tabs

### Visual style
- dark navy / blue background
- subtle border at bottom
- active tab highlighted with pill style or underlined indicator
- compact but premium spacing

---

## Main Screen Layout
The **Main** tab should be the user’s primary entry point.

### Top section: dual upload cards
Show **two upload cards side by side**:

#### Left card
**Upload Assessment**
- primary upload area
- drag-and-drop support
- browse button
- show uploaded filename after upload

#### Right card
**Upload Answer Key (Optional)**
- optional upload area
- helper text: improves evaluation quality / scoring
- show uploaded filename after upload

### Design notes
- both cards should have equal visual weight
- keep them large enough for comfortable interaction
- use dashed borders or subtle card outlines
- include upload icon

---

## Assessment Preview Section
Once an assessment is uploaded, reveal a preview section below the uploads.

### Section title
**Assessment Preview**

### Behavior
- show embedded preview of uploaded PDF
- ideally show first page preview immediately
- support page navigation if possible
- if full viewer is too heavy, show a first-page snapshot + `Open full preview`

### Recommendation
Use `react-pdf` / `pdf.js` for rendering.

### Layout
- large card container
- top bar with filename, page count, and small actions
- optional small actions: zoom, open, expand

---

## Shielding Methods Section
After upload, reveal a new section:

### Title
**Choose Shielding Method**

Use a collapsible / expandable section if needed, but the UI should still feel simple.

### Layout
Display **5 method tiles/cards** in a grid.

Methods:
- ICW
- Dual Layer
- Font Attack
- ICW + Dual Layer
- ICW + Font

### Important wording change
In the interface, prefer the label:
**Shielding Methods**
instead of:
**Attack Methods**

The system is a protective defense product, so the language should align with that framing.

### Each tile should include
- method name
- 1-line description
- optional tag such as `Recommended` if relevant
- selected / unselected visual state

### Example short descriptions
- **ICW** — In-context watermark perturbation
- **Dual Layer** — Overlay and hidden-layer protection
- **Font Attack** — Glyph and font-level perturbation
- **ICW + Dual Layer** — Combined contextual and layered shielding
- **ICW + Font** — Combined contextual and font-based shielding

### Tile behavior
- tiles should be clickable
- only one selection at a time unless multi-select is intentionally supported
- selected tile should have strong highlight, glow, border, or accent background
- after a method is selected, reveal the next step

---

## Run Call-To-Action
After method selection, reveal a strong action area.

### Title / helper text
**Ready to run IntegrityShield**

### CTA button
`Run Shielding Pipeline`

### Button state
- disabled until assessment uploaded and shielding method selected
- optional tooltip when disabled

### Supporting text
Provide short, confidence-building helper text such as:
> IntegrityShield will extract the document, apply the selected shielding method, compile the protected PDF, and generate the evaluation results.

---

## Pipeline Run Tab
The `Pipeline Run` tab should show the system workflow in a clean, visually guided format.

Do not overload it with raw logs unless Developer Mode is enabled.

### Main content
Show a **pipeline stage tracker**.

Suggested stages:
1. PDF Ingestion
2. Document Extraction
3. Perturbation Planning
4. Shield Injection
5. PDF Compilation
6. Evaluation

### Each stage should show
- stage number
- stage title
- short description
- status badge

### Status badges
Use:
- `Queued`
- `Running`
- `Completed`
- `Failed`

### Visual approach
Prefer one of these:
- vertical stepper
- horizontal progress tracker
- timeline with stage cards

### Recommendation
A vertical stepper with stage cards will likely be the cleanest.

### Per-stage details
For each stage, optionally show:
- status icon
- execution time
- completion timestamp
- expand / collapse for more details

But keep these hidden unless relevant or Developer Mode is ON.

---

## Developer Mode Behavior
When `Developer Mode` is ON:
- show event logs
- show stage timing
- show raw evaluation metadata
- show file paths / technical diagnostics where safe
- show extracted low-level metrics

When `Developer Mode` is OFF:
- hide logs completely
- hide engineering-only metadata
- keep only user-friendly progress states

### Suggested implementation
Use a side drawer, bottom panel, or expandable diagnostics card for developer content.
Avoid placing logs directly in the main flow.

---

## Results Tab
The `Results` tab should focus on outcomes, not process.

### Top layout
Use a two-column comparison layout:

#### Left
**Original Assessment**
- embedded preview card

#### Right
**Shielded Assessment**
- embedded preview card

### Below comparison
Show a dedicated **Detection Report** or **Protection Report** card.

Suggested sections:
- shielding method used
- pipeline completion status
- detection success / prevention summary
- evaluation summary
- downloadable artifacts

### Possible result cards
- `Protection Summary`
- `Detection Report`
- `Generated Files`
- `Evaluation Metrics`

### Example result metrics to show in user-friendly form
- method applied
- protected PDF generated
- evaluation completed
- report available

If you want quantitative metrics, keep them readable and polished.
For example:
- Detection Accuracy
- Prevention Success Rate
- False Positive Rate
- Variant Count

Do not overload the results page with raw tables unless Developer Mode is enabled.

---

## Recommended Screen Structure

### Main tab
1. Header / step indicator
2. Upload cards
3. Assessment preview
4. Shielding methods
5. Run CTA

### Pipeline Run tab
1. Stage tracker
2. Optional per-stage details
3. Developer diagnostics panel when toggle is ON

### Results tab
1. Original vs Shielded preview
2. Detection / Protection report
3. Download artifacts
4. Developer metrics if toggle is ON

---

## Step Progress Indicator
Add a step progress strip near the top of the Main tab.

Suggested steps:
- Upload
- Configure
- Run
- Results

### Behavior
Highlight the current step.
This immediately tells users where they are in the workflow.

---

## Visual Design System

### Style direction
The UI should feel:
- secure
- minimal
- intelligent
- modern
- professional
- research-demo ready

### Theme
Keep the dark theme, but refine it.

#### Suggested palette direction
- deep navy / midnight blue background
- slightly lighter cards
- cyan / teal / blue accent
- green for success states
- amber for running states
- red only for failure / errors

### Cards
- rounded corners
- subtle border
- soft shadow / glow
- enough padding for breathing room

### Typography
- clear hierarchy
- bold section titles
- muted helper text
- strong contrast for important labels

### Spacing
Increase whitespace between sections.
The current UI feels a little compressed.
A more breathable layout will instantly look more premium.

---

## UI Content Wording Recommendations
Use more polished wording throughout.

### Replace
- `Attack variants`
with
- `Generated Shielded Variants`

### Replace
- `Attack methods`
with
- `Shielding Methods`

### Replace
- `Run Summary`
with
- `Pipeline Summary`

### Replace
- `Evaluation`
with
- `Protection Evaluation`

### Replace
- `Original PDF`
with
- `Original Assessment`

---

## Interaction Guidelines

### Before upload
Show only:
- upload cards
- minimal helper text
- disabled downstream sections or hidden sections

### After upload
Reveal:
- preview
- shielding method selection

### After method selection
Reveal:
- run button
- short explanation of what happens next

### During run
- switch focus to Pipeline Run tab automatically or prompt user to open it
- show animated progress states
- keep the experience calm and readable

### After completion
- show success state
- guide user to Results tab
- optionally show banner: `Shielded assessment and report are ready`

---

## Suggested React Component Breakdown

### Layout / structure
- `AppShell`
- `TopHeader`
- `TabNavigation`
- `StatusIndicator`
- `DeveloperModeToggle`

### Main tab
- `UploadSection`
- `UploadCard`
- `AssessmentPreviewCard`
- `ShieldingMethodGrid`
- `ShieldingMethodTile`
- `RunPipelineCard`
- `StepProgressBar`

### Pipeline tab
- `PipelineStageTracker`
- `PipelineStageCard`
- `StageStatusBadge`
- `DeveloperDiagnosticsPanel`
- `EventLogViewer`

### Results tab
- `ResultComparisonPanel`
- `PdfPreviewCard`
- `ProtectionReportCard`
- `MetricsSummaryGrid`
- `ArtifactDownloadPanel`

---

## Recommended State Model
At a high level, the UI state should track:
- uploaded assessment file
- uploaded answer key file
- preview availability
- selected shielding method
- pipeline status
- per-stage statuses
- results availability
- developer mode on/off

Example high-level state:
- `assessmentFile`
- `answerKeyFile`
- `selectedMethod`
- `pipelineStatus`
- `stageStatuses`
- `results`
- `developerMode`

---

## Suggested Empty States

### No assessment uploaded
> Upload an assessment PDF to begin shielding and evaluation.

### No answer key uploaded
> Optional: upload an answer key to improve evaluation quality.

### No method selected
> Choose one shielding method to configure the pipeline.

### No results yet
> Run the pipeline to generate the shielded PDF and protection report.

---

## Suggested Micro-Interactions
Use subtle interactions to improve perceived quality:
- tile hover elevation
- animated tab underline
- smooth expand/collapse for sections
- soft fade-in when preview appears
- progress pulse while stage is running
- success check animation after completion

Keep these subtle, not flashy.

---

## Important Product Framing Note
This system should visually emphasize:
- protecting assessments
- preserving academic integrity
- secure processing of educational documents

Do not make the interface feel like a generic offensive attack platform.
That is why language, iconography, and progressive workflow matter.

Use shield / document / lock / verification visual cues, not hacker-style cues.

---

## Suggested Homepage Flow Summary
The final Main screen should feel like this:

1. User lands on a clean interface
2. Upload Assessment and Upload Answer Key are clearly visible side by side
3. Assessment preview appears after upload
4. User selects a shielding method from clean method tiles
5. Run button appears and feels obvious
6. Pipeline tab shows system progress
7. Results tab shows final shielded document and report

This makes the system feel guided, deliberate, and product-ready.

---

## Final Recommendation for Cursor
Build this as a **React-based multi-tab workflow UI** using reusable components and progressive disclosure.

### Technical preferences
- React
- Tailwind CSS
- componentized cards and tabs
- `react-pdf` for preview
- Framer Motion for subtle transitions
- clean state-driven rendering

### High-level implementation goal
Transform the current layout into a polished workflow experience that is:
- easier for first-time users
- cleaner for demos
- better aligned with the IntegrityShield brand
- scalable for future capabilities

---

## One-Sentence Design Brief
Design IntegrityShield as a premium, dark-themed, workflow-based document protection interface where users upload an assessment, choose a shielding method, monitor the pipeline, and review the protected output in a clean and intuitive multi-tab React experience.

