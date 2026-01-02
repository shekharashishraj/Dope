# Perturbation Application Analysis

## Summary

**Issue**: Not all perturbations from the perturbation JSON files were applied to the documents.

## Findings

### Document 1: `machine_learning_graduate_doc_01`

**Expected Perturbations:**
- Total questions: 20
- Questions with perturbations: 10 (questions 1-10)
- Perturbations per question: 3
- Total perturbations available: 30

**Actually Applied:**
- Replacements applied: **10** (1 per question)
- Questions processed: 10 (questions 1-10)
- Questions skipped: 10 (questions 11-20 have empty `perturbations: []` arrays)

**Status**: ✅ **Working as designed** - Only 1 perturbation per question is applied (the first one), and questions 11-20 have no perturbations in the source JSON.

### Document 2: `machine_learning_graduate_doc_02`

**Expected Perturbations:**
- Total questions: 20
- Questions with perturbations: **20** (all questions)
- Perturbations per question: 3
- Total perturbations available: **60**

**Actually Applied (Before Fix):**
- Replacements applied: **2** (only questions 1 and 16)
- Questions processed: 2
- Questions skipped: **18** (questions 2-15, 17-20)

**Status (Before Fix)**: ❌ **ANOMALY DETECTED** - Only 2 out of 20 questions had perturbations applied.

**Status (After Fix)**: ✅ **FIXED** - Extraction function now correctly identifies all 20 questions. The system should now apply perturbations to all questions that have valid perturbations in the JSON.

## Root Cause Analysis

### Why Only 1 Perturbation Per Question?

The `DualLayerInjector` code (lines 84-103 in `src/injection/dual_layer_injector.py`) is **intentionally designed** to only use the **first perturbation per question** by default:

```python
# Use only the FIRST perturbation per question to avoid overlapping replacements
# Multiple perturbations (k=3) would create overlapping/adjacent replacements
# that cause malformed LaTeX. For dual-layer, we only need one replacement per question.
```

This is **expected behavior** to avoid:
- Overlapping replacements
- Malformed LaTeX
- Position conflicts

### Why Only 2 Perturbations Applied in doc_02?

The code skips a question if:
1. **No perturbations available** (line 89-91)
2. **No latex_stem_text found** (line 112-113)
3. **Stem text not found in LaTeX** (line 128-130)
4. **Original substring not found within stem** (line 177-178)

For `machine_learning_graduate_doc_02`, only questions 1 and 16 succeeded. The other 18 questions likely failed at one of these steps:
- The `latex_stem_text` in the perturbation JSON doesn't match the actual LaTeX content
- The `original_substring` cannot be found within the stem text
- Text normalization/whitespace differences

## Specific Issues Found

### Issue 1: Mismatched `latex_stem_text`

Looking at the perturbation JSON for doc_02, many perturbations have `latex_stem_text` that doesn't match the actual question text. For example:

- Question 2: `latex_stem_text` is `"True, True"` (an answer option) instead of the actual question stem
- Question 3: `latex_stem_text` is `"False, False"` instead of the question
- Question 6: `latex_stem_text` is from a different question entirely

This causes the stem text search to fail (line 117-130), so those questions are skipped.

### Issue 2: Position-Based Matching

The code uses `start_pos` and `end_pos` from the perturbation (relative to `latex_stem_text`), but if the `latex_stem_text` is wrong, the positions are also wrong, causing the substring search to fail.

## Solution Implemented ✅

**Answer to your question**: No, we don't necessarily need the `latex_stem_text` from the LLM! 

We've implemented a **comprehensive solution** that:
1. First tries to use `latex_stem_text` from the perturbation JSON (if provided by LLM)
2. If that doesn't match, **automatically extracts** the correct `latex_stem_text` directly from the LaTeX file by question number
3. Uses the extracted text to find and apply perturbations
4. **Supports question-level substitutions** - substitutions can be in the question stem itself
5. **Supports option-level substitutions** - substitutions can be in the answer options (with fallback search)

This makes the system much more robust - even if the LLM provides incorrect `latex_stem_text`, the injector will automatically fix it by extracting the correct text from the LaTeX.

### Changes Made

**Modified Files:**
- `src/latex_parser.py` - **Fixed extraction function** to properly handle nested enumerate environments
  - Now correctly extracts all questions (tested: 20/20 for doc_02)
  - Handles both MCQ (with nested enumerate) and TF (without nested enumerate) questions
  - Uses depth tracking to identify top-level question items
- `src/injection/dual_layer_injector.py` - Added fallback extraction and question-level support
  - Automatic extraction when JSON `latex_stem_text` is incorrect
  - Question-level substitution support (substitutions in question stems)
  - Option-level substitution support (searches in options when not found in stem)
- `src/injection/font_attack_injector.py` - Added same fallback mechanism

**How It Works:**
```python
# If JSON latex_stem_text doesn't match, extract from LaTeX by question number
if not stem_pos:
    extracted_stem = extract_question_stem_from_latex(mutated_tex, question_number)
    if extracted_stem:
        # Try to find the extracted stem in the LaTeX
        stem_pos = self._find_question_stem_in_tex(mutated_tex, extracted_stem)
        if stem_pos:
            latex_stem_text = extracted_stem  # Use the correct stem text

# Search for original_substring in stem, or fallback to options
if not found in stem:
    # Search in nested enumerate (options) for option-level substitutions
    nested_begin = find_nested_enumerate_after_stem()
    if found in options:
        apply_substitution_in_options()
```

### Benefits

1. **No need to fix perturbation JSON files** - The system auto-corrects incorrect `latex_stem_text`
2. **More reliable** - Uses the actual LaTeX content as the source of truth
3. **Backward compatible** - Still works with correct `latex_stem_text` from JSON
4. **Automatic** - No manual intervention needed
5. **Question-level support** - Handles substitutions in question stems (not just options)
6. **Robust extraction** - Correctly parses LaTeX with nested structures

## Recommendations

### Immediate Fixes (Optional - Now Less Critical)

1. **Verify `latex_stem_text` in perturbation JSON files** (Optional)
   - The fallback mechanism handles incorrect values, but correct values are still preferred
   - Can help with debugging and logging

2. **Add better logging** (Already improved)
   - Now logs when fallback extraction is used
   - Logs which questions are being skipped and why
   - Logs when stem text is not found

3. **Improve text matching** (Already improved)
   - Fallback extraction handles most cases
   - Normalize whitespace more aggressively (if needed)
   - Try partial matches if exact match fails (if needed)

### Long-term Improvements

1. **Enable multiple perturbations per question** (if needed)
   - Set `config.experimental.dual_layer_allow_multiple_perturbations = True`
   - Be aware this may cause overlapping replacements

2. **Fix perturbation generation**
   - Ensure `latex_stem_text` is correctly extracted from LaTeX
   - Verify positions are relative to the correct text

3. **Add validation step**
   - Before applying perturbations, validate that:
     - `latex_stem_text` exists in the LaTeX
     - `original_substring` exists within the stem text
     - Positions are valid

## Verification Steps

To verify the fix:

1. Check the LaTeX files to see if the stem text exists
2. Compare `latex_stem_text` in JSON with actual LaTeX content
3. Check logs for warnings about skipped questions
4. Manually verify a few failed questions to understand the mismatch

## Files to Check

- `src/injection/dual_layer_injector.py` - Main injection logic
- `output_perturbation/20260102_115118/machine_learning/graduate/machine_learning_graduate_doc_02/machine_learning_graduate_doc_02_perturbation.json` - Source perturbations
- `output_attacked_pdfs/20260102_115848/machine_learning/Graduate/machine_learning_graduate_doc_02/dual_layer/machine_learning_graduate_doc_02_dual_layer.tex` - Generated LaTeX
- Compilation logs for any errors

