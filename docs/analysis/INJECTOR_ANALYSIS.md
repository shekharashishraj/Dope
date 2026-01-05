# Injector Analysis - 2026-01-02

## Summary

**Status**: ❌ **Injectors are NOT working correctly**

The fix I implemented (extracting `latex_stem_text` from LaTeX) has a bug in the extraction function itself.

## What Happened

### Expected Behavior
- Document 1: 10 replacements applied ✅ (working)
- Document 2: Should have 20 replacements applied ❌ (only 2 applied)

### Actual Results (20260102_121820)
- Document 1: 10 replacements ✅
- Document 2: **Only 2 replacements** (questions 1 and 16) ❌

## Root Cause

### Issue 1: Incorrect `latex_stem_text` in JSON ✅ FIXED
- The LLM-generated `latex_stem_text` was wrong (e.g., "True, True" instead of question stem)
- **Solution**: Added fallback to extract from LaTeX by question number

### Issue 2: LaTeX Extraction Function Has Bug ❌ NOT FIXED YET
- The `extract_question_stem_from_latex()` function is extracting **nested option items** instead of question stems
- For question 2, it extracts "True, True" (first option) instead of "Suppose your model is overfitting..."
- The regex pattern doesn't properly handle nested `\begin{enumerate}` environments

### Issue 3: Original Substring Mismatch
- Even if we fix the extraction, some perturbations have `original_substring` that is an **option** (e.g., "Increase the amount of training data.") 
- But we're searching for it in the **question stem**, where it doesn't exist
- The `start_pos` and `end_pos` in perturbations are relative to `latex_stem_text`, but if `latex_stem_text` is wrong, positions are also wrong

## Current State

### Extraction Function Status
- ❌ Still extracting wrong text (nested items instead of stems)
- The pattern `r'\\item\s+(?:True or False:\s+)?(.*?)\\begin\{enumerate\}'` matches:
  - Question stems correctly ✅
  - But also matches nested option items ❌

### Why Only 2 Questions Worked
1. **Question 1**: `latex_stem_text` from JSON happened to be correct, or extraction worked
2. **Question 16**: Similar - either JSON was correct or extraction worked
3. **Questions 2-15, 17-20**: Extraction failed, returning nested option text instead of question stems

## Next Steps

### Immediate Fix Needed

1. **Fix `extract_question_stem_from_latex()` function**
   - Need to properly track enumerate depth
   - Only match top-level `\item` entries (question stems)
   - Exclude nested `\item` entries (options)

2. **Handle Option-Based Perturbations**
   - Some perturbations target **options**, not question stems
   - Need to search in the correct location (options vs stem)
   - May need to extract options separately

3. **Improve Position Matching**
   - When `latex_stem_text` is corrected, positions may be wrong
   - Need better fallback to find `original_substring` even if positions are off

### Testing

After fixing, test with:
```bash
python3 -c "
from src.latex_parser import extract_question_stem_from_latex
with open('output/machine_learning/graduate/latex_documents/machine_learning_graduate_doc_02.tex', 'r') as f:
    tex = f.read()
    for q in [1, 2, 3, 4, 5, 16]:
        stem = extract_question_stem_from_latex(tex, q)
        print(f'Q{q}: {stem[:80] if stem else \"None\"}...')
"
```

Expected output should show actual question stems, not options.

## Files Modified

- ✅ `src/injection/dual_layer_injector.py` - Added fallback extraction
- ✅ `src/injection/font_attack_injector.py` - Added fallback extraction  
- ❌ `src/latex_parser.py` - Extraction function still has bug

## Detection Results

From `output_detection/20260102_121849`:
- **Detection Rate**: 32.5% (13/40 questions detected)
- **False Negative Rate**: 67.5% (27/40 not detected)
- This is expected given only 12 total perturbations were applied (10 + 2) out of potentially 60+

The low detection rate is likely because:
1. Most perturbations weren't applied (only 12/60+)
2. Some applied perturbations may not have been effective
3. Detection method may need improvement

