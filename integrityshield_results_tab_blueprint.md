# IntegrityShield Results Tab Blueprint

## Goal
Redesign the **Results** tab so it feels like a polished analysis dashboard rather than a text-heavy output screen.

The page should help users immediately understand:
- what was generated
- whether shielding worked
- what the evaluation outcome was
- which files are available

The current side-by-side document preview is good and should remain the visual anchor at the top of the page.

---

## Core Design Direction
Keep the top comparison preview, but redesign everything below it into a **structured results dashboard** with clearer visual hierarchy, stronger summary cards, better grouping, and less verbose text.

The screen should answer three questions quickly:
1. What happened?
2. Did shielding work?
3. What can I inspect or download?

---

## Recommended Page Structure

```text
┌────────────────────────────────────────────────────────────────────┐
│ Results                                                            │
│                                                                    │
│ [ Original Assessment ]   [ Shielded Assessment ]                  │
│                                                                    │
│ [ Protection Overview metric cards ]                               │
│                                                                    │
│ [ Detection Results ] [ Evaluation Breakdown / Chart ]             │
│                                                                    │
│ [ Question-Level Results ]                                         │
│                                                                    │
│ [ Pipeline Timeline ]                                              │
│                                                                    │
│ [ Artifacts ]                                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 1. Keep the Side-by-Side PDF Comparison at the Top
This is already one of the strongest parts of the screen.

### Recommended cards
- **Original Assessment**
- **Shielded Assessment**

### Small improvements
Add a footer row with actions such as:
- Open
- Download
- Expand preview

### Suggested enhancements
- show filename in a muted metadata row
- keep preview frame height consistent
- add subtle label badge such as `Original` and `Shielded`

This section should remain the top focal point.

---

## 2. Replace the Current Pipeline Summary with Metric Cards
The current summary card is too text-heavy and wastes space.

### Important wording improvement
Instead of long strings like:
- `Generated 1 perturbations for 10 questions`

Use short metrics only.

### Recommended metric cards
Show 4 to 6 compact cards in a row or responsive grid.

Suggested metrics:
- **Questions Extracted** → `10`
- **Perturbations** → `1`
- **Shielding Method** → `Dual Layer`
- **PDF Compilation** → `Enabled`
- **Runtime** → `510.9s`
- **Generated Variants** → `1`

### Example layout
```text
[ Questions ] [ Perturbations ] [ Method ] [ Runtime ]
     10              1          Dual Layer   510.9s
```

### Why this works
- easier to scan
- reduces reading effort
- uses space better
- feels like a dashboard instead of logs

---

## 3. Add a Protection Overview Card
Below the preview or metric cards, add a high-level summary card that explains the outcome.

### Title
**Protection Overview**

### Example content
- Shielding method used
- Number of questions processed
- Whether shielded PDF was generated successfully
- Whether evaluation completed successfully

### Example copy
**Protection Overview**  
Dual Layer shielding was applied successfully to 10 extracted questions. The protected PDF was generated and evaluated.

This helps the page feel more narrative and less mechanical.

---

## 4. Redesign Protection Evaluation into a Split Visual Section
The current `Protection Evaluation` block has too much text and not enough visual structure.

### Recommended layout
Use a 2-column layout:

#### Left column
A compact stat grid

#### Right column
A visual chart

### Suggested stat cards / rows
- Total Questions
- Detected
- Not Detected
- Refused
- Detection Rate
- False Negative Rate
- Average Confidence

### Recommended visualization
Add a small chart such as:
- donut chart
- ring chart
- horizontal stacked bar

### Best chart option
A **donut chart** showing:
- Detected
- Not Detected
- Refused

This instantly improves readability.

---

## 5. Improve Metric Formatting
Be careful with formatting.

### Recommended fixes
- show percentages with `%`
- keep decimals consistent
- use short labels
- avoid full sentence values

### Example
Use:
- `Detection Rate: 0%`
- `False Negative Rate: 100%`

Not:
- `False Negative Rate: 100`

---

## 6. Break Down Evaluation into Clearly Named Subsections
Instead of a single large `Protection Evaluation` block, break it into smaller sub-sections.

### Recommended subsections
- **Overview**
- **By Parsing Method**
- **By Question Type**
- **Sample Detection Results**

This creates better visual rhythm and helps users mentally parse the page.

---

## 7. Redesign “By Parsing Method” as Compact Comparison Cards
The current parsing method section is still too list-like.

### Recommended layout
Use one or more compact cards.

Example:
```text
┌──────────────────────────────┐
│ LLM Judge                    │
│ Total Questions: 10          │
│ Detected: 0                  │
│ Not Detected: 10             │
│ Refused: 0                   │
│ Detection Rate: 0%           │
└──────────────────────────────┘
```

If more parsing methods are added later, this layout scales nicely.

---

## 8. Redesign “By Question Type” as Small Metric Tiles
For question type breakdowns such as MCQ, do not use large text blocks.

### Better approach
Use a compact tile.

Example:
```text
[ MCQ ]
Total: 10
Detected: 0
Refused: 0
Detection Rate: 0%
```

If multiple question types exist later, they can appear in a row.

---

## 9. Improve Sample Detection Results
This section is useful, but visually repetitive and too long.

### Recommended approach
Convert each question result into a compact row card with strong status signaling.

### Each row should include
- question number
- question type badge
- confidence
- detection status icon
- one-line summary

### Example row
```text
❌ Question 1    [MCQ]    Confidence: 0.00
AI answer matches gold answer.
```

### Status icon guidance
- `✅` detected
- `❌` not detected
- `⚠` refused

### Important UX improvement
Show only the first 3–5 sample rows by default, then add:
- `Show all results`
- `Expand all`

This reduces page fatigue.

---

## 10. Add Filtering for Question-Level Results (Optional but Strong)
If feasible, add simple controls above sample detection results:
- All
- Detected
- Not Detected
- Refused

This makes the section much more usable as the number of questions grows.

---

## 11. Add a Pipeline Timeline Section
Instead of a plain `Status` list, redesign it as a visual timeline.

### Title
**Pipeline Timeline**

### Example structure
```text
✔ Upload Complete
✔ Document Extraction Complete
✔ Perturbation Plan Generated
✔ Shielded PDF Compiled
✔ Evaluation Complete
```

### Optional metadata
- time
- duration

This section creates a much better narrative of what happened.

### Recommendation
Use a vertical timeline with icons and timestamps.

---

## 12. Redesign the Artifacts Section
The artifacts section is valuable but currently too plain.

### Recommended structure
Group artifacts by stage, but use file cards or rows with file-type badges and actions.

### Example
**Document Extraction**
- `CSE476_Quiz2.json`  `[JSON]`  `[Download]`
- `CSE476_Quiz2.tex`   `[TEX]`   `[Download]`

**Perturbation Planning**
- `CSE476_Quiz2_perturbation.json` `[JSON]` `[Download]`

**Shield Injection**
- `CSE476_Quiz2_dual_layer_final.pdf` `[PDF]` `[Open] [Download]`

**Evaluation**
- `detection_report.txt` `[TXT]` `[Download]`

### Visual guidance
- use file icons
- use rounded badges for file types
- align actions consistently to the right

This will make the artifacts section feel much more finished.

---

## 13. Better Use of Horizontal Space
Right now many cards span full width with sparse content.

### Use a dashboard layout
Below the preview area, use responsive sections like:

```text
[ Metric cards grid ]

[ Detection overview ] [ Chart ]

[ Parsing method ] [ Question type ]

[ Timeline ]

[ Sample results ]

[ Artifacts ]
```

This creates denser, more meaningful use of the layout.

---

## 14. Recommended Visual Hierarchy
The page should follow this order of importance:

1. Original vs Shielded comparison
2. Protection outcome and core metrics
3. Evaluation summary
4. Question-level examples
5. Timeline and artifacts

That hierarchy ensures users see the most important information first.

---

## 15. Recommended Section Titles
Use stronger, more product-friendly labels.

### Suggested naming
- `Pipeline Summary` → **Pipeline Overview**
- `Status` → **Pipeline Timeline**
- `Protection Evaluation` → **Evaluation Overview**
- `Sample Detection Results` → **Question-Level Results**
- `Artifacts` → **Generated Artifacts**

These names feel clearer and less like internal debug output.

---

## 16. Add Icons Throughout
Icons will help the page feel more polished and easier to scan.

### Suggested icon pairings
- Protection Overview → shield icon
- Evaluation Overview → chart icon
- Question-Level Results → list/check icon
- Timeline → clock/history icon
- Artifacts → file stack/download icon

If using Lucide icons, consider:
- `ShieldCheck`
- `BarChart3`
- `ListChecks`
- `Clock3`
- `Files`
- `Download`

---

## 17. Recommended Components

### Top comparison
- `DocumentComparisonPanel`
- `PdfPreviewCard`

### Metrics / overview
- `ResultMetricCard`
- `ProtectionOverviewCard`
- `PipelineOverviewGrid`

### Evaluation
- `EvaluationSummaryCard`
- `DetectionDonutChart`
- `ParsingMethodCard`
- `QuestionTypeTile`

### Question-level results
- `QuestionResultRow`
- `QuestionResultList`
- `QuestionResultFilterBar`

### Timeline / artifacts
- `PipelineTimeline`
- `TimelineEvent`
- `ArtifactGroupCard`
- `ArtifactRow`

---

## 18. Suggested React Layout Breakdown

### Desktop layout
```text
Top Row:
[ Original Assessment ] [ Shielded Assessment ]

Second Row:
[ Metric Cards x4 or x6 ]

Third Row:
[ Evaluation Overview ] [ Outcome Chart ]

Fourth Row:
[ Parsing Method Cards ] [ Question Type Tiles ]

Fifth Row:
[ Question-Level Results ]

Sixth Row:
[ Pipeline Timeline ]

Seventh Row:
[ Generated Artifacts ]
```

### Mobile / narrow layout
Stack sections vertically in the same order.

---

## 19. Suggested Micro-Interactions
Use subtle motion to improve quality.

### Recommended
- hover state for artifact rows
- chart tooltip on hover
- expand/collapse for question results
- copy filename action for artifacts
- smooth section appearance after pipeline completion

Keep interactions subtle and professional.

---

## 20. Developer Mode Handling
When `Developer Mode` is OFF:
- keep summaries high-level
- hide raw logs
- hide deep internal metrics

When `Developer Mode` is ON:
- reveal deeper evaluation details
- show confidence distributions
- show more complete sample results
- show richer artifact metadata

The default results page should stay clean and readable.

---

## 21. Cursor Implementation Brief
Implement the Results tab as a **dashboard-style analysis page**.

### Requirements
- keep top side-by-side PDF comparison
- replace text-heavy summary with compact metric cards
- shorten verbose values like perturbation descriptions to just numbers
- add a protection overview card
- redesign evaluation section into stat cards + chart
- convert question-level sample results into compact status rows
- add a visual pipeline timeline
- redesign artifacts into grouped file rows/cards with badges and actions
- use responsive two-column sections where appropriate
- keep dark theme consistent with IntegrityShield branding

---

## 22. One-Sentence Design Brief
Design the Results tab as a polished, dark-themed analysis dashboard where users can compare the original and shielded assessment, quickly understand protection outcomes through metric cards and charts, review question-level results, and access generated artifacts in a clean, structured layout.

