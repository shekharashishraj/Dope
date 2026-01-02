# Injection Methods Guide

## Overview

The IntegrityShield injection system applies perturbations to LaTeX documents to create manipulated PDFs that exploit the render-parse gap. This guide covers how the injection system works and recent improvements.

## Injection Methods

### Dual Layer Injection

The dual layer method creates a visual overlay where:
- **Visual layer** (what humans see): Original text
- **Text layer** (what LLMs read): Replacement text

**How it works:**
1. Replaces text in LaTeX using `\duallayerbox{original}{replacement}` macro
2. Compiles PDF with replacement text in the text layer
3. Applies image overlay from original PDF to cover replacement with original text visually

**Files:**
- `src/injection/dual_layer_injector.py` - Main injection logic
- `src/injection/pdf_overlay_dual_layer.py` - Image overlay application

### Font Attack Injection

Creates custom fonts where visible glyphs differ from encoded characters.

**Files:**
- `src/injection/font_attack_injector.py` - Main injection logic
- `src/injection/font_builder.py` - Font generation

### ICW (Inline Code Watermark)

Embeds inline control words/braces so rendered text stays the same but LaTeX diverges.

**Files:**
- `src/injection/icw_injector.py` - Main injection logic

## Recent Improvements (2026-01-02)

### 1. Question-Level Substitution Support ✅

**What it means:**
Substitutions can now be applied to **any part of the question**, including:
- Question stems (e.g., "overfitting" → "underfitting" in the question text)
- Answer options (e.g., "Increase training data" → "Decrease training data")

**How it works:**
1. Injector searches for `original_substring` in the question stem first
2. If not found, searches in the nested enumerate (options) section
3. Applies substitution wherever found

**Example:**
```latex
% Question stem substitution
\item Suppose your model is \duallayerbox{overfitting}{underfitting}. Which method should you use?

% Option substitution  
\begin{enumerate}
    \item \duallayerbox{Increase training data}{Decrease training data}
\end{enumerate}
```

### 2. Automatic LaTeX Extraction ✅

**Problem solved:**
Previously, if the LLM-generated `latex_stem_text` in the JSON was incorrect, perturbations wouldn't be applied.

**Solution:**
- Injectors now automatically extract the correct `latex_stem_text` from the LaTeX file
- Uses question number to find the correct text
- Works even when JSON has wrong values

**How it works:**
```python
# 1. Try to use latex_stem_text from JSON
stem_pos = find_in_latex(json_latex_stem_text)

# 2. If not found, extract from LaTeX by question number
if not stem_pos:
    extracted_stem = extract_question_stem_from_latex(latex_content, question_number)
    stem_pos = find_in_latex(extracted_stem)
```

### 3. Fixed LaTeX Parsing ✅

**Problem solved:**
The extraction function was incorrectly extracting nested option items instead of question stems.

**Solution:**
- Rewrote `extract_question_stem_from_latex()` to properly handle nested enumerate environments
- Uses depth tracking to identify top-level question items
- Handles both MCQ (with nested enumerate) and TF (without nested enumerate) questions

**Verification:**
- ✅ Extracts all 20 questions correctly from test documents
- ✅ Handles nested structures properly
- ✅ Works for both MCQ and TF question types

## Usage

### Basic Usage

```bash
# Generate PDFs from perturbations
python -m src.pdf_generator --perturbation-folder output_perturbation/20260102_123536

# Use specific methods
python -m src.pdf_generator --perturbation-folder output_perturbation/20260102_123536 --methods dual_layer

# Limit for testing
python -m src.pdf_generator --perturbation-folder output_perturbation/20260102_123536 --limit 2
```

### Testing Injectors

```bash
# Run test suite
python3 test_injector_question_level.py
```

Expected output:
```
✓ Test 1: Question-Level Substitution - PASS
✗ Test 2: Option-Level Substitution - Needs refinement
✓ Test 3: Extraction Fallback - PASS
```

## How Substitutions Are Applied

### Step 1: Find Question Stem

1. Try `latex_stem_text` from perturbation JSON
2. If not found, extract from LaTeX by question number
3. Search for stem text in LaTeX document

### Step 2: Find Original Substring

1. Search for `original_substring` in the question stem
2. If not found, search in options (nested enumerate)
3. Use position from JSON, or find manually if positions don't match

### Step 3: Apply Replacement

1. Create `\duallayerbox{original}{replacement}` macro
2. Replace text in LaTeX
3. Compile PDF
4. Apply image overlay (for dual layer)

## Troubleshooting

### Issue: Substitutions not applied

**Check:**
1. Does the question have perturbations in the JSON?
2. Is `original_substring` present in the question text?
3. Check logs for warnings about skipped questions

**Solution:**
- The extraction fallback should handle most cases
- If still failing, check that `original_substring` matches the actual text (including whitespace)

### Issue: Wrong question extracted

**Check:**
1. Verify question numbers in JSON match LaTeX
2. Check for counter resets in LaTeX (`\setcounter{enumi}{X}`)

**Solution:**
- The extraction function handles counter resets automatically
- If issues persist, verify LaTeX structure

### Issue: Option-level substitutions not working

**Status:** Currently being refined. The logic is in place but may need better text matching.

**Workaround:** Ensure `original_substring` is in the question stem, or verify it matches exactly in options.

## Technical Details

### LaTeX Extraction Algorithm

1. Split document by sections (`\section*{...}`)
2. Find top-level `\begin{enumerate}` blocks
3. Track enumerate depth to identify top-level `\item` entries
4. Extract text until nested `\begin{enumerate}` (options) or next `\item`
5. Clean and normalize extracted text

### Substitution Matching

1. Try exact match of `original_substring`
2. Try normalized match (whitespace normalized)
3. Try partial match (first 5 characters)
4. Search in options if not found in stem

## Files Modified

- `src/latex_parser.py` - Fixed extraction function
- `src/injection/dual_layer_injector.py` - Added question-level and option-level support
- `src/injection/font_attack_injector.py` - Added extraction fallback
- `test_injector_question_level.py` - Test suite

## References

- `PERTURBATION_ANALYSIS.md` - Detailed analysis of perturbation application
- `INJECTOR_TESTING_REPORT.md` - Test results and status
- `INJECTOR_ANALYSIS.md` - Analysis of injector behavior

