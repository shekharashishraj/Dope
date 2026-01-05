# Font Attack Generation Analysis

## Problem Summary

Font attack PDFs are **not being generated** for `cybersecurity_undergraduate_doc_01` in the `20251228_144329` run.

## Root Cause

**The document has NO perturbations at all** - all 16 questions have empty `perturbations: []` arrays.

### Why No Perturbations Were Generated

Looking at the perturbation generation log (`logs/perturbation_20251228_144124.log`):

1. **Line 191**: `ERROR - Failed to parse JSON response: Invalid \escape: line 4 column 28 (char 58)`
2. **Line 196**: The API response contained LaTeX strings with unescaped backslashes: `"latex_stem_text": "1. \_\_\_\_\_\_\_\_\_ framework..."`
3. **Line 204**: `Parsed 0 total perturbations in 0.00 seconds`

**The Issue**: The LLM returned JSON with invalid escape sequences. In JSON, `\_` is not a valid escape sequence - it should be `\\_`. The `json.loads()` call failed, resulting in 0 perturbations being parsed.

**Comparison with doc_02**:
- doc_02's response was valid JSON → 36 perturbations parsed successfully
- doc_01's response had invalid JSON → 0 perturbations parsed

### Evidence

1. **Perturbation JSON Analysis:**
   - File: `output_perturbation/20251228_144124/cybersecurity/undergraduate/cybersecurity_undergraduate_doc_01/cybersecurity_undergraduate_doc_01_perturbation.json`
   - Total questions: 16
   - Questions with perturbations: **0**
   - Questions without perturbations: **16**

2. **Orchestrator Logic:**
   - For font_attack methods, the orchestrator loops through perturbation indices 1, 2, 3
   - For each index, it filters questions to only include those with at least that many perturbations
   - If no questions have perturbations, all indices are skipped
   - Result: No font_attack folder is created, no PDFs are generated

3. **Comparison with doc_02:**
   - `cybersecurity_undergraduate_doc_02` **does have perturbations**
   - Result: Font attack PDFs **are generated** successfully (1font, 2font, 3font)

## Code Flow

```
Orchestrator.process_document()
  └─> For font_attack methods:
      └─> Loop pert_idx in [1, 2, 3]:
          └─> Filter questions: only those with >= pert_idx perturbations
          └─> If filtered_questions is empty:
              └─> Skip this pert_idx (continue)
          └─> Otherwise:
              └─> Initialize injector
              └─> Apply injection
              └─> Generate fonts
              └─> Compile PDF
              └─> Add to perturbation_results
      └─> If perturbation_results is empty:
          └─> Result marked as success=True but total_perturbations=0
          └─> No folder/files created
```

## Why This Happens

The font attack generation **depends entirely on perturbations existing** in the JSON file. If the perturbation generation step:
- Failed
- Was skipped
- Produced no valid perturbations

Then font attack cannot generate any PDFs.

## Solution

### Immediate Fixes (Applied)

1. **Improved error handling in `orchestrator.py`**:
   - When no perturbations are found, the result is now marked as `success: False` with a clear error message
   - Added warning messages to help diagnose the issue

2. **Fixed JSON parsing in `openai_client.py`**:
   - Added automatic fix for unescaped LaTeX backslashes in JSON responses
   - When `json.loads()` fails due to `\_` sequences, the code now attempts to fix them by escaping properly (`\_` → `\\_`)
   - This prevents the parsing failure that caused 0 perturbations to be extracted

### Long-term Fix Needed

1. **Investigate why perturbations weren't generated for doc_01:**
   - Check perturbation generation logs
   - Verify if there were validation errors
   - Check if questions were skipped during perturbation generation

2. **Improve error visibility:**
   - Add logging when perturbation JSON has no perturbations
   - Add validation step before processing documents
   - Warn users early if document has insufficient perturbations

3. **Consider graceful degradation:**
   - For font_attack, if some questions have perturbations but not all, still generate PDFs for those that do
   - Currently, if ALL questions have no perturbations, nothing is generated (correct behavior)

## Testing

Run the analysis script to check any document:
```bash
python3 analyze_font_attack_issue.py
```

## Files Modified

1. `src/injection/orchestrator.py` - Improved error handling for empty perturbation results
2. `src/openai_client.py` - Fixed JSON parsing to handle unescaped LaTeX backslashes (`\_` → `\\_`)
3. `analyze_font_attack_issue.py` - Analysis script to diagnose perturbation issues

## Conclusion

**The font attack code is working correctly.** The issue is that `cybersecurity_undergraduate_doc_01` has no perturbations to apply. The real problem is in the perturbation generation step, not the font attack injection step.

