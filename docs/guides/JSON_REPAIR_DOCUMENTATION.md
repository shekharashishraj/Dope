# JSON Repair Functionality Documentation

## Overview

The JSON repair functionality handles cases where GPT-5.1 generates invalid JSON, particularly when it outputs word numbers (e.g., "fifty") instead of numeric values (e.g., 50). This document describes the repair mechanisms and how they work.

## Problem Statement

### Issue

GPT-5.1 sometimes generates JSON with word numbers in numeric contexts:

```json
{
  "question_index": 1,
  "start_pos": fifty,  // ❌ Invalid - should be: 50
  "end_pos": 60
}
```

This causes `json.loads()` to fail with:
```
JSONDecodeError: Expecting value: line X column Y
```

### Impact

When JSON parsing fails:
- No perturbations are extracted from the API response
- All questions show 0 perturbations
- The batch processing appears to succeed but produces no results

## Solution Architecture

### Multi-Layer Repair Strategy

The repair process uses a layered approach:

1. **Word Number Repair** - Converts word numbers to numeric values
2. **Escape Sequence Repair** - Fixes invalid escape sequences
3. **Individual Object Extraction** - Extracts valid objects from malformed arrays
4. **Array Pattern Extraction** - Final fallback to extract array structure

### Repair Flow

```
API Response
    ↓
Standard JSON Parse (attempt 1)
    ↓ (if fails)
Word Number Repair
    ↓
Escape Sequence Repair
    ↓
JSON Parse (attempt 2)
    ↓ (if fails)
Extract Individual Objects
    ↓ (if fails)
Extract Array Pattern
    ↓
Return Valid Perturbations
```

## Implementation Details

### Word Number Repair (`_repair_json_word_numbers`)

**Location**: `src/openai_client.py`

**Purpose**: Converts word numbers to numeric values in JSON

**Algorithm**:
1. Track string boundaries (inside/outside quotes)
2. Detect word numbers after colons (in value positions)
3. Replace word numbers with numeric equivalents
4. Preserve string values (don't modify text inside quotes)

**Supported Word Numbers**:

```python
word_to_number = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
    'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
    'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
    'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
    'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
    'eighty': '80', 'ninety': '90', 'hundred': '100', 'thousand': '1000'
}
```

**Example**:

```json
// Before repair:
{
  "start_pos": fifty,
  "end_pos": sixty
}

// After repair:
{
  "start_pos": 50,
  "end_pos": 60
}
```

**Key Features**:
- Only processes outside string values
- Handles multiple spaces after colons
- Stops at commas, braces, brackets, or newlines
- Case-insensitive matching

### Escape Sequence Repair (`_repair_json_escapes`)

**Location**: `src/openai_client.py`

**Purpose**: Fixes invalid escape sequences in JSON strings

**Handles**:
- Invalid escapes like `\_` → `\\_`
- Unicode escape sequences
- Trailing backslashes

**Example**:

```json
// Before repair:
{
  "text": "This is a test\_string"
}

// After repair:
{
  "text": "This is a test\\_string"
}
```

### Individual Object Extraction

**Purpose**: Extract valid JSON objects even if the array is malformed

**Algorithm**:
1. Use regex to find object patterns: `\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}`
2. Try to parse each object individually
3. Repair each object if needed
4. Validate against PerturbationMapping model
5. Return all valid objects

**Example**:

```json
// Malformed array:
[
  {"question_index": 1, "start_pos": 0, "end_pos": 5},
  {"question_index": 2, "start_pos": fifty, "end_pos": 60},  // Invalid
  {"question_index": 3, "start_pos": 10, "end_pos": 15}
]

// After extraction:
[
  {"question_index": 1, "start_pos": 0, "end_pos": 5},      // Valid
  {"question_index": 3, "start_pos": 10, "end_pos": 15}     // Valid
  // Question 2 skipped due to invalid JSON
]
```

### Array Pattern Extraction

**Purpose**: Final fallback to extract array structure from text

**Algorithm**:
1. Use regex to find array pattern: `\[.*\]`
2. Repair the extracted array
3. Parse and validate

## Usage

### Automatic Repair

The repair happens automatically during API response parsing:

```python
# In _call_api_with_retry():
try:
    parsed = json.loads(content_clean)
except json.JSONDecodeError as json_err:
    # Automatic repair
    repaired_content = self._repair_json_word_numbers(content_clean)
    repaired_content = self._repair_json_escapes(repaired_content)
    parsed = json.loads(repaired_content)
```

### Manual Repair

You can also use the repair functions directly:

```python
from src.openai_client import OpenAIClient

client = OpenAIClient(config)
repaired_json = client._repair_json_word_numbers(invalid_json)
```

## Error Handling

### Logging

The repair process logs warnings and errors:

```
WARNING: Initial JSON parse failed: Expecting value: line 425 column 19
INFO: Successfully parsed JSON after repair
```

### Fallback Behavior

If all repair attempts fail:
- Individual valid objects are extracted and returned
- Invalid objects are skipped with a warning
- Empty list is returned if no valid objects found

## Testing

### Test Cases

1. **Word Numbers**: `"start_pos": fifty` → `"start_pos": 50`
2. **Multiple Spaces**: `"start_pos":  fifty` → `"start_pos": 50`
3. **Mixed Valid/Invalid**: Extract valid objects from malformed array
4. **String Preservation**: Don't modify word numbers inside string values

### Example Test

```python
invalid_json = '{"start_pos": fifty, "end_pos": 60}'
repaired = client._repair_json_word_numbers(invalid_json)
# Result: '{"start_pos": 50, "end_pos": 60}'
```

## Limitations

### Current Limitations

1. **Compound Numbers**: Does not handle "twenty-five" or "one hundred"
2. **Complex Expressions**: Does not handle arithmetic expressions
3. **Nested Structures**: Complex nested JSON may not be fully repaired

### Future Enhancements

1. Add support for compound numbers
2. Handle arithmetic expressions (e.g., "fifty plus ten")
3. Improve nested structure handling

## Performance

### Time Complexity

- Word number repair: O(n) where n is JSON string length
- Escape sequence repair: O(n)
- Individual object extraction: O(m) where m is number of objects

### Space Complexity

- O(n) for storing repaired JSON string

## Best Practices

1. **Always validate** parsed JSON against the PerturbationMapping model
2. **Log warnings** when repair is needed to track model behavior
3. **Monitor repair frequency** to identify patterns in model output
4. **Update word dictionary** if new patterns emerge

## Troubleshooting

### Issue: Word numbers not being repaired

**Check**:
1. Is the word in the `word_to_number` dictionary?
2. Is it in a numeric context (after colon, before comma/brace)?
3. Is it inside a string value (shouldn't be repaired)?

### Issue: Repair creates invalid JSON

**Solution**: The repair functions are designed to be safe, but edge cases may exist. Check the logs for specific error messages.

### Issue: Some objects still fail validation

**Solution**: This is expected - invalid objects are skipped. Check the validation errors in logs to understand why.

## References

- JSON Specification: https://www.json.org/
- Python json module: https://docs.python.org/3/library/json.html

