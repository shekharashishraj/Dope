# GPT-5.1 Model Implementation Documentation

## Overview

This document describes the implementation of GPT-5.1 model support in the IntegrityShield pipeline. The implementation includes model configuration, API parameter handling, JSON repair functionality, and prompt template updates.

## Table of Contents

1. [Model Configuration](#model-configuration)
2. [API Parameter Changes](#api-parameter-changes)
3. [JSON Repair Functionality](#json-repair-functionality)
4. [Prompt Template Updates](#prompt-template-updates)
5. [Testing and Verification](#testing-and-verification)

---

## Model Configuration

### Config File (`config/config.yaml`)

The configuration has been updated to use `gpt-5.1-2025-11-13` as the default model:

```yaml
openai:
  model: "gpt-5.1-2025-11-13"
  # ... other settings ...
  # GPT-5.1 specific parameters
  reasoning_effort: "medium"  # none, low, medium, high
  verbosity: "medium"  # low, medium, high
```

**Note**: The traditional parameters (`temperature`, `top_p`, `frequency_penalty`, `presence_penalty`, `max_tokens`, `logprobs`) are kept for backward compatibility but are not used for GPT-5.1 models.

### Configuration Model (`src/models/config.py`)

Added new fields to `OpenAIConfig`:

```python
class OpenAIConfig(BaseModel):
    # ... existing fields ...
    # GPT-5.1 parameters
    reasoning_effort: Optional[str] = Field(default=None, description="Reasoning effort for GPT-5.1 models: none, low, medium, high")
    verbosity: Optional[str] = Field(default=None, description="Verbosity for GPT-5.1 models: low, medium, high")
    
    def is_gpt5_model(self) -> bool:
        """Check if the model is a GPT-5.x model."""
        return self.model.startswith("gpt-5")
```

---

## API Parameter Changes

### GPT-5.1 Parameter Differences

GPT-5.1 models use different API parameters compared to traditional GPT models:

**Deprecated Parameters (not used for GPT-5.1):**
- `temperature`
- `top_p`
- `frequency_penalty`
- `presence_penalty`
- `max_tokens`
- `logprobs`
- `top_logprobs`

**New Parameters (for GPT-5.1):**
- `reasoning`: Dictionary with `effort` key (values: "none", "low", "medium", "high")
- `verbosity`: String (values: "low", "medium", "high")

**Current Limitation**: The OpenAI Python SDK does not yet support `reasoning` and `verbosity` parameters. These are configured but not passed to the API. The model will use default values. When the SDK is updated, these parameters can be uncommented in the code.

### Implementation Details

#### OpenAI Client (`src/openai_client.py`)

The `OpenAIClient` class now conditionally handles parameters based on the model:

```python
def _is_gpt5_model(self) -> bool:
    """Check if the model is a GPT-5.x model."""
    return self.config.openai.is_gpt5_model()

# In _call_api_with_retry():
if self._is_gpt5_model():
    # For now, don't pass reasoning/verbosity as SDK doesn't support them
    # TODO: Add these parameters when SDK is updated
    pass
else:
    # Use traditional parameters for non-GPT-5 models
    api_params["temperature"] = self.temperature
    # ... other traditional parameters ...
```

**Locations Updated:**
1. `_call_api_with_retry()` - Main API call method
2. `create_batch_file()` - Batch file creation for batch API

#### Response Collector (`src/detection/response_collector.py`)

The `ResponseCollector` class also conditionally handles parameters:

```python
def _is_gpt5_model(self) -> bool:
    """Check if the model is a GPT-5.x model."""
    return self.model.startswith("gpt-5")

# In _call_api_with_retry_file_id():
if self._is_gpt5_model():
    # GPT-5.1 models don't use max_tokens
    # TODO: Add reasoning/verbosity when SDK supports them
    pass
else:
    api_params["max_tokens"] = 2000
```

---

## JSON Repair Functionality

### Problem

GPT-5.1 sometimes generates invalid JSON with word numbers instead of numeric values:
- `"start_pos": fifty,` instead of `"start_pos": 50,`
- This causes JSON parsing to fail, resulting in 0 perturbations being extracted

### Solution

Added `_repair_json_word_numbers()` method to convert word numbers to numeric values before JSON parsing.

#### Implementation (`src/openai_client.py`)

```python
def _repair_json_word_numbers(self, json_str: str) -> str:
    """
    Repair JSON by converting word numbers to numeric values.
    
    Handles cases where the model outputs words like "fifty" instead of 50.
    Only converts words that appear in numeric contexts (after colons, before commas).
    """
    # Dictionary mapping word numbers to their numeric values
    word_to_number = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
        'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
        'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
        'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
        'eighty': '80', 'ninety': '90', 'hundred': '100', 'thousand': '1000'
    }
    
    # Uses state machine to track string boundaries
    # Only converts word numbers outside of string values
    # Pattern: ": word," or ": word\n" or ": word}" where word is a number word
```

#### Supported Word Numbers

The repair function supports:
- Basic numbers: zero through nineteen
- Tens: twenty, thirty, forty, fifty, sixty, seventy, eighty, ninety
- Hundreds and thousands: hundred, thousand

#### JSON Parsing Flow

The updated parsing flow:

1. **First attempt**: Standard JSON parsing
2. **If fails**: Repair word numbers → Repair escape sequences → Parse again
3. **If still fails**: Extract individual valid JSON objects from the array
4. **Final fallback**: Extract array pattern and repair it

```python
try:
    parsed = json.loads(content_clean)
except json.JSONDecodeError as json_err:
    # Repair word numbers first
    repaired_content = self._repair_json_word_numbers(content_clean)
    # Then repair escape sequences
    repaired_content = self._repair_json_escapes(repaired_content)
    parsed = json.loads(repaired_content)
```

---

## Prompt Template Updates

### Grouped Batch v3 TF Prompt (`prompts/grouped_batch_v3/tf_grouped_prompt.py`)

The prompt template was restructured to work with grouped batch queries while maintaining the original content structure.

#### Key Changes

1. **Removed single-question placeholders** from main template:
   - `{latex_stem_text}`
   - `{gold_answer}`
   - `{question_type}`
   - `{reasoning_steps}`
   - `{copyable_text}`
   - `{prefix_note}`
   - `{answer_guidance}`
   - `{retry_instructions}`
   - `{question_index}`

2. **Kept only shared placeholders**:
   - `{questions_list}` - List of formatted questions
   - `{k}` - Number of mappings per question
   - `{total_mappings}` - Total expected mappings

3. **Generalized instructions** - All instructions apply to all questions in the batch

#### Template Structure

```
## SITUATION:
[General situation description]

## Role:
[Role description]

##Task:
[General task instructions that apply to all questions]

### VALIDATION RULES:
[Rules that apply to all questions]

### TRUTH-FLIPPING TECHNIQUES:
[Techniques with examples]

### DOMAIN-SPECIFIC FEW-SHOT EXAMPLES:
[Examples from various domains]

### MANDATORY RULES:
[Rules that apply to all questions]

## TF QUESTIONS

{questions_list}  # Individual questions formatted here

## OUTPUT FORMAT

[Output format instructions]
```

#### Question Formatting

Individual questions are formatted by `format_tf_question_entry_v2()`:

```python
def format_tf_question_entry_v2(
    question_index: int,
    latex_stem_text: str,
    copyable_text: str,
    gold_answer: str,
    k: int = 3
) -> str:
    """Format a single TF question entry for grouped batch prompt v2."""
    flipped_answer = "False" if gold_answer == "True" else "True"
    return f"""**Question {question_index}:**
- LaTeX stem: `{latex_stem_text}`
- Copyable text: {copyable_text}
- Gold answer: {gold_answer} (MUST flip to {flipped_answer} - use Tier 1 techniques)
- ⚠️ CRITICAL: Your perturbation MUST cause the AI to answer {flipped_answer}. If it's too weak, detection will FAIL.
- Goal: Generate {k} mappings using Tier 1 directional inversions (increases↔decreases, greater↔less, positive↔negative, etc.)

"""
```

---

## Testing and Verification

### Verification Script

A small verification script (`verify_gpt5_changes.py`) was used during the GPT‑5.1 rollout to check config and client wiring. It is **not shipped in the repository** (keep a local copy if you still use it; see `.gitignore`). When present, it verifies:

```bash
python3 verify_gpt5_changes.py
```

This script verifies:
1. Config YAML has correct model and parameters
2. Config model has new fields and helper method
3. OpenAI client has GPT-5.1 handling
4. Response collector has GPT-5.1 handling

### Test Results

The implementation has been tested and verified:
- ✅ Config loads correctly with GPT-5.1 model
- ✅ Model detection works correctly
- ✅ API calls work without deprecated parameters
- ✅ JSON repair handles word numbers
- ✅ Prompt templates work with grouped batches

### Known Limitations

1. **SDK Support**: The OpenAI Python SDK does not yet support `reasoning` and `verbosity` parameters. These are configured but not passed to the API. The model uses default values.

2. **Word Number Repair**: The repair function handles common word numbers (zero through ninety, hundred, thousand). More complex number words (e.g., "twenty-five") are not currently supported but can be added if needed.

---

## Migration Guide

### Upgrading to GPT-5.1

1. **Update config.yaml**:
   ```yaml
   openai:
     model: "gpt-5.1-2025-11-13"
     reasoning_effort: "medium"
     verbosity: "medium"
   ```

2. **No code changes needed** - The code automatically detects GPT-5.1 models and handles parameters accordingly.

3. **When SDK supports reasoning/verbosity**:
   - Uncomment the TODO sections in `src/openai_client.py` and `src/detection/response_collector.py`
   - The parameters will then be passed to the API

### Downgrading to GPT-4

Simply change the model in `config.yaml`:
```yaml
openai:
  model: "gpt-4o"
```

The code will automatically use traditional parameters.

---

## File Changes Summary

### Modified Files

1. **`config/config.yaml`**
   - Changed model to `gpt-5.1-2025-11-13`
   - Added `reasoning_effort` and `verbosity` parameters

2. **`src/models/config.py`**
   - Added `reasoning_effort` and `verbosity` fields
   - Added `is_gpt5_model()` helper method

3. **`src/openai_client.py`**
   - Added `_is_gpt5_model()` method
   - Updated `_call_api_with_retry()` to conditionally handle parameters
   - Updated `create_batch_file()` to conditionally handle parameters
   - Added `_repair_json_word_numbers()` method
   - Enhanced JSON parsing with word number repair

4. **`src/detection/response_collector.py`**
   - Added `_is_gpt5_model()` method
   - Updated `_call_api_with_retry_file_id()` to conditionally handle parameters
   - Added reasoning_effort and verbosity initialization

5. **`prompts/grouped_batch_v3/tf_grouped_prompt.py`**
   - Restructured template to work with grouped batches
   - Removed single-question placeholders
   - Maintained original content structure

### New Files

1. **`verify_gpt5_changes.py`** - Optional local verification script (not committed; see `.gitignore`)

---

## Troubleshooting

### Issue: JSON parsing fails with word numbers

**Solution**: The `_repair_json_word_numbers()` method should handle this automatically. If you encounter new word number patterns, add them to the `word_to_number` dictionary.

### Issue: API calls fail with "unexpected keyword argument"

**Solution**: This should not happen as deprecated parameters are excluded for GPT-5.1. If it does, check that `_is_gpt5_model()` is working correctly.

### Issue: Reasoning/verbosity parameters not working

**Solution**: This is expected - the SDK doesn't support them yet. They will work once the SDK is updated. The model uses default values in the meantime.

---

## Future Enhancements

1. **SDK Update**: When OpenAI Python SDK supports `reasoning` and `verbosity`, uncomment the TODO sections to enable them.

2. **Enhanced Word Number Support**: Add support for compound numbers (e.g., "twenty-five", "one hundred").

3. **Better Error Handling**: Add more specific error messages for JSON parsing failures.

---

## References

- OpenAI GPT-5.1 Documentation: https://platform.openai.com/docs/models/gpt-5.1
- OpenAI Python SDK: https://github.com/openai/openai-python

---

## Changelog

### 2026-01-02
- Initial GPT-5.1 implementation
- Added JSON word number repair
- Updated prompt templates for grouped batches
- Added verification script

