# Injector Testing Report - Question-Level Substitutions

## Summary

✅ **Question-level substitutions work correctly**
✅ **Extraction fallback works correctly**  
⚠️ **Option-level substitutions need refinement** (currently searches in options but may need better matching)

## Test Results

### Test 1: Question-Level Substitution ✅ PASS
- **Test**: Substitution in question stem (e.g., "overfitting" → "underfitting")
- **Result**: ✓ PASS - Correctly applied `\duallayerbox{overfitting}{underfitting}`
- **Status**: Working as expected

### Test 2: Option-Level Substitution ⚠️ NEEDS WORK
- **Test**: Substitution in options (e.g., "Increase training data" → "Decrease training data")
- **Result**: ✗ FAIL - Not finding substring in options section
- **Status**: Logic added but needs debugging. The injector now searches in options when not found in stem, but matching may need improvement.

### Test 3: Extraction Fallback ✅ PASS
- **Test**: Incorrect `latex_stem_text` in JSON, should extract from LaTeX
- **Result**: ✓ PASS - Successfully extracted correct stem and applied substitution
- **Status**: Working as expected

## Implementation Status

### ✅ Completed

1. **Fixed LaTeX Extraction Function**
   - Now correctly extracts all 20 questions from doc_02
   - Handles both MCQ (with nested enumerate) and TF (without nested enumerate)
   - Uses depth tracking to identify top-level items

2. **Question-Level Substitutions**
   - Injectors correctly handle substitutions in question stems
   - Searches for `original_substring` within the extracted `latex_stem_text`
   - Applies `\duallayerbox` macro correctly

3. **Extraction Fallback**
   - When `latex_stem_text` from JSON doesn't match, automatically extracts from LaTeX
   - Uses question number to find correct stem text
   - Works even when JSON has incorrect values

### ⚠️ In Progress

1. **Option-Level Substitutions**
   - Logic added to search in options when not found in stem
   - Currently not matching correctly - needs debugging
   - May need better text normalization or matching strategy

## Key Improvements Made

1. **Robust LaTeX Parsing**
   - Fixed `extract_question_stem_from_latex()` to handle nested enumerates
   - Now extracts all questions correctly (tested: 20/20 for doc_02)

2. **Fallback Mechanism**
   - Injectors automatically extract correct `latex_stem_text` when JSON is wrong
   - No manual fixes needed for incorrect JSON files

3. **Question-Level Support**
   - Injectors handle substitutions in question stems
   - Works with both correct and incorrect `latex_stem_text` from JSON

## Next Steps

1. **Debug Option-Level Substitutions**
   - Verify the options search logic is being executed
   - Improve text matching in nested enumerate environments
   - Test with real perturbation data

2. **Comprehensive Testing**
   - Test with actual perturbation JSON files
   - Verify all 20 questions in doc_02 can have substitutions applied
   - Test both question-level and option-level substitutions

3. **Documentation**
   - Document that substitutions can be at question level
   - Update code comments to reflect option-level support

## Files Modified

- ✅ `src/latex_parser.py` - Fixed extraction to handle nested enumerates
- ✅ `src/injection/dual_layer_injector.py` - Added question-level and option-level support
- ✅ `src/injection/font_attack_injector.py` - Added extraction fallback
- ✅ `test_injector_question_level.py` - Test suite for verification

## Verification

Run tests with:
```bash
python3 test_injector_question_level.py
```

Expected: 2/3 tests pass (question-level and extraction fallback work, option-level needs work)

