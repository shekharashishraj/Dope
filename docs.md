# IntegrityShield Documentation

This repository now bundles both **perturbation generation** (LLM-powered) and
**document-layer injection** (ICW, dual-layer, font attack). Use this document as
an onboarding reference for practitioners extending or operating the stack.

## 1. Perturbation Pipeline

### Flow
1. Discover JSON assessments under `output/<domain>/<level>/`.
2. Read the paired LaTeX source specified in `file_paths.latex_file`.
3. For every question, extract the LaTeX stem and build prompts per type (MCQ,
   TF, Long).
4. Batch prompt GPT-4o (configurable) to obtain perturbation mappings.
5. Merge the perturbations back into the JSON and save with `_perturbation`
   suffix under `JSON_output_perturbation/`.

### Command
```bash
python -m src.processor [--limit N] [--force] [--config config/custom.yaml]
```
Key CLI flags are documented in `README.md`. Configuration lives in
`config/config.yaml` (batch size, retries, temperature, etc.).

### Important Modules
- `src/processor.py`: orchestrates batching and prompt dispatch.
- `src/openai_client.py`: batched GPT calls + retry logic.
- `src/file_handler.py`: JSON I/O + resume support.
- `src/latex_parser.py`: stem extraction helpers (handles nested enumerate environments).

### Output Layout
```
output/<domain>/<level>/JSON_output_perturbation/<doc>_perturbation.json
```
Each question gains a `perturbations` list containing the original substring,
replacement substring, offsets, and reasoning.

## 2. Injection Pipeline

Once perturbations exist, the injection suite renders deceptive LaTeX/PDFs.
`src/injection` contains:
- `orchestrator.py`: common entry point used by CLI/tests.
- `icw_injector.py`, `dual_layer_injector.py`, `font_attack_injector.py`, plus
  hybrid combinations.
- `pdf_dual_layer.py`, `pdf_overlay_dual_layer.py`: image overlay utilities.

### Command (multi-document test)
```bash
python3 -m src.injection_tester
```
This script picks perturbation JSON files, runs every injector, generates
injected LaTeX and PDFs, and writes logs to
`output/<domain>/<level>/injected_<method>/`.

### Direct Usage
Instantiate `InjectionOrchestrator` and call `process_document` with a path to a
single perturbation JSON and a list of methods. Set `compile_pdf=False` for
faster dry runs.

### Output Layout
```
output/<domain>/<level>/injected_<method>/
    <doc>_<method>.tex / .pdf / _compile.log
    fonts_<n>/ (font attack only)
```
Each method maintains its own subdirectory so you can compare effects.

## 3. Injection Methods

| Method | Key Files | Description | Notes |
| ------ | --------- | ----------- | ----- |
| `icw` (Inline Code Watermark) | `src/injection/icw_injector.py` | Embeds inline control words/braces so the rendered text stays the same but the underlying LaTeX diverges. | Runs with PDFLaTeX; minimal asset requirements. |
| `dual_layer` | `src/injection/dual_layer_injector.py`, `src/injection/pdf_dual_layer.py`, `src/injection/pdf_overlay_dual_layer.py` | Produces image overlays aligned to the original text, placing the manipulated visual layer above the original text layer. | Requires accurate bounding boxes; outputs multi-layer PDFs. |
| `font_attack` | `src/injection/font_attack_injector.py`, `src/injection/font_builder.py` | Builds custom fonts so the visible glyphs differ from the encoded characters (render–parse gap). | Needs XeLaTeX and generated fonts; described below. |
| `icw_dual_layer`, `icw_font_attack` | `src/injection/hybrid_injectors.py` | Runs ICW first, then dual-layer or font attack for compounded defenses. | Debug in stages; inherits requirements of both techniques. |

All injectors inherit from `BaseInjector` (shared helpers for locating stems,
editing the preamble, etc.) and are registered inside
`InjectionOrchestrator.INJECTION_METHODS`.

### Injection Improvements (2026-01-02)

**Question-Level Substitution Support:**
- Injectors now handle substitutions in question stems (not just options)
- Substitutions can target any part of the question text
- Works with both correct and incorrect `latex_stem_text` from JSON

**Automatic LaTeX Extraction:**
- If `latex_stem_text` from JSON doesn't match, injectors automatically extract the correct text from LaTeX
- Uses question number to find the correct stem text
- Handles both MCQ (with nested enumerate) and TF (without nested enumerate) questions
- Fixed extraction function to properly parse nested LaTeX structures

**Robust Text Matching:**
- Searches for `original_substring` in question stem first
- Falls back to searching in options (for option-level substitutions)
- Normalizes whitespace for better matching
- Handles position mismatches gracefully

**Key Features:**
- ✅ Question-level substitutions (in question stems)
- ✅ Option-level substitutions (in answer options)
- ✅ Automatic extraction fallback (when JSON is incorrect)
- ✅ Robust LaTeX parsing (handles nested structures)
- ✅ All 20 questions correctly extracted and processed

## 4. Font Attack Details

Font attack manipulates the render/parse gap using custom TrueType fonts. The
workflow is:

1. **Planning** (`FontAttackInjector`)
   - `_find_question_stem_in_tex` locates the substring to manipulate.
   - `_build_attack_plan` maps hidden characters (replacement text) to visual
     characters (original text), even when lengths differ.
   - `_split_hidden_text_for_words` ensures multi-word spans keep proper spacing.
   - `_render_plan` registers LaTeX fragments and queued fonts.

2. **Font Generation** (`FontBuilder`)
   - Duplicates `resources/fonts/Roboto-Regular.ttf` per attack position.
   - Supports multi-character composites and zero-width glyphs to hide leftovers.
   - Saves fonts to `fonts_<n>/faXXXX_posY.ttf` and copies the base font.

3. **Compilation**
   - Copy the desired fonts directory to `fonts/` and run XeLaTeX:
     ```bash
     cd output/<domain>/<level>/injected_font_attack
     rm -rf fonts && cp -R fonts_1 fonts
     xelatex -interaction=nonstopmode <doc>_font_attack_1font.tex
     ```
   - Examine `_compile.log` for missing font or XeTeX issues.

4. **Validation**
   - Open the PDF to confirm visuals remain unchanged.
   - Run `pdftotext <pdf> - | rg "<replacement>"` or copy/paste the relevant
     string to ensure the text layer now reflects the perturbation.

## 5. Testing & Verification

| Goal | Command / Notes |
| ---- | ---------------- |
| Rebuild perturbations for a subset | `python -m src.processor --limit N` |
| Full injection smoke test | `python3 -m src.injection_tester` (long runtime) |
| Targeted injection experiment | Write a short script instantiating
`FontAttackInjector` with chosen questions (see `tmp_font_q2`, `tmp_font_q11`) |
| Visual vs parse check | `pdftotext <pdf>` and manual copy/paste |

## 6. Troubleshooting & Ops Tips

- **Missing substrings**: The injector will skip mappings it cannot locate in
  the LaTeX. However, the system now automatically extracts correct `latex_stem_text`
  when JSON is wrong, so this should be rare. Check logs for extraction fallback messages.
- **Question-level substitutions**: Substitutions can now be in question stems or options.
  The injector searches in both locations automatically.
- **XeTeX errors**: Ensure the `fonts/` directory exists next to the `.tex` file
  before compiling font-attack documents.
- **Large builds**: Font attack can create hundreds of `.ttf` files; delete
  unused `fonts_*` folders to save space.
- **Resume perturbations**: Use `--force` to regenerate outputs if a JSON changes.
- **Testing artifacts**: Clean `tmp_font_*` directories after ad-hoc experiments.
- **Extraction issues**: If questions aren't being extracted, verify LaTeX structure.
  The extraction function handles nested enumerates, but complex structures may need review.

## 7. Future Enhancements

- Share a font cache across documents to avoid rebuilding identical glyphs.
- Parameterize per-word splitting thresholds (e.g., only split when there are
  more than *n* hidden characters per word).
- Automate copy/paste verification with a PDF parser.
- Extend `injection_tester` to emit structured metrics (success counts, timing,
  MLLM refusal simulations).

Use this document alongside `README.md` for day-to-day operations. Contributions
that touch perturbation prompts or injection logic should update both references.
