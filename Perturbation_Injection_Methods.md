## Generating Attacked HTML Assessment Webpages

### Baseline Generation (No Attack Content)
1. Normalize source exam JSON into a canonical schema (`data/exam_content.json`).
2. Render baseline HTML/CSS from the normalized JSON into:
   - `out/baseline/<domain>/<education_level>/exam.html`
   - `out/baseline/<domain>/<education_level>/styles.css`
The baseline is a clean, semantically structured DOM (question cards with `data-qid`, `data-qtype`) with no hidden instructions.

### Attack Family 1: Hidden Instructions (CSS-Hidden Prompt Injection)
We generate 9 attacked variants by inserting a single hidden `<div>` at the beginning of `<body>`.
The injected element includes a marker token `PHANTOM_TEST_TOKEN_<attack_id>` and an adversarial instruction string, while CSS makes it visually hidden.
The 9 CSS techniques are: `display_none`, `opacity_zero`, `offscreen`, `clip_zero`, `zindex_overlay`, `color_match`, `visibility_hidden`, `sr_only`, and `tiny_text`.
Outputs are written to:
`out/attacked/<domain>/<education_level>/hidden_instructions/exam__<attack_id>.html`.

### Attack Family 2: CSS Inline Span Overlay (Render/Parse Mismatch)
This attack wraps selected substrings in each question prompt using nested spans:
`<span class="c<hash>"><span class="orig">ORIGINAL</span><span class="r">REPLACEMENT</span></span>`.
CSS positions `.r` absolutely over `.orig` but makes it transparent, while `.orig` remains visible and non-selectable.
A companion JS file (`width_calc.js`) sets container widths to stabilize overlay alignment.
Outputs are written to:
`out/attacked/<domain>/<education_level>/css_before/`.

### Attack Family 3: Image/Canvas Attack (Screen + Print-Safe Extension)
This attack replaces prompt text in the DOM with a perturbed version, stores the original text in `data-original-text`, and renders the original text visually as a canvas overlay positioned over the prompt.
For printing/PDF generation, a print occlusion layer adds print-specific CSS and `beforeprint`/`afterprint` JS hooks that draw opaque canvases over the prompt region so the printed page shows the original text visually while the DOM still contains the perturbed text.
Outputs are written to:
- `out/attacked/<domain>/<education_level>/image_canvas/exam.html` (screen)
- `out/attacked/<domain>/<education_level>/image_canvas/exam_printsafe.html` (print-safe)