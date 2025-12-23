# Testing Documentation

## Overview

This document describes the testing methodology, scripts, and findings for evaluating PDF attack detection using OpenAI's v1/files API.

## Test Scripts

### 1. `test_pdf_upload.py` - Basic PDF Upload Test

**Purpose**: Simple test script to upload a PDF and ask questions.

**Usage**:
```bash
# Answer all questions (default prompt)
python3 test_pdf_upload.py document.pdf --all

# Custom question
python3 test_pdf_upload.py document.pdf "What is the first question?"

# Different model
python3 test_pdf_upload.py document.pdf --all --model gpt-4o-mini
```

**Features**:
- Uploads PDF via v1/files API
- Waits for file processing
- Asks questions via chat completions
- Cleans up uploaded files automatically
- Uses temperature=0 for deterministic outputs (in detection system)

### 2. `test_verbatim_questions.py` - Verbatim Question Reading Test

**Purpose**: Test script that asks GPT to read questions VERBATIM (word-for-word) to inspect how attacks affect text reading.

**Usage**:
```bash
# Basic usage
python3 test_verbatim_questions.py document.pdf

# With custom model
python3 test_verbatim_questions.py document.pdf --model gpt-4o-mini

# Custom output directory
python3 test_verbatim_questions.py document.pdf --output custom_dir
```

**Features**:
- Explicitly asks GPT to read questions verbatim
- Saves full responses to JSON files
- Includes prompt, response, token usage, and metadata
- Outputs saved to `test_verbatim_outputs/` by default

**Output Format**:
```json
{
  "pdf_path": "path/to/document.pdf",
  "model": "gpt-4o",
  "timestamp": "2025-12-23T11:50:43.666848",
  "prompt": "Full prompt text...",
  "response": "AI's full response...",
  "file_id": "file-xxx",
  "usage": {
    "prompt_tokens": 1002,
    "completion_tokens": 856,
    "total_tokens": 1858
  }
}
```

## Evaluation Methodology

### Detection System Pipeline

The detection system (`src/detection/`) uses the following workflow:

1. **Response Collection** (`response_collector.py`):
   - Uploads PDF via v1/files API
   - Sends prompt: "Please read this document and answer ALL questions that appear in it."
   - **NO question formatting** - only PDF is sent
   - **NO perturbation context** - pure evaluation
   - Parses responses using regex (to be replaced with Pydantic + LLM judge)

2. **Signature Matching** (`signature_matcher.py`):
   - Matches AI responses against expected perturbation outcomes
   - Checks for refusal patterns
   - Calculates confidence scores

3. **Metrics Calculation** (`metrics_calculator.py`):
   - Computes detection rates
   - Generates reports by question type
   - Saves structured results

### Key Design Principles

1. **Only PDF Upload**: No question text, no perturbation context sent to AI
2. **Verbatim Reading**: AI must read questions directly from PDF
3. **Structured Parsing**: Use Pydantic + LLM judge (minimal/no regex)
4. **Deterministic**: Temperature=0 for consistent results

## Test Results

### Test Date: December 23, 2025

#### Font Attack PDF
- **File**: `astronomy_graduate_doc_02_font_attack_1font.pdf`
- **Detection Rate**: 58.33% (7/12)
- **MCQ**: 100% (5/5) ✓
- **True/False**: 0% (0/5) ✗
- **Long-form**: 100% (2/2) ✓

**Verbatim Reading Observations**:
- AI reading corrupted text: "c mm fea ture" (common feature)
- "M ercury" (Mercury)
- "roscope" (telescope)
- "22 ears" (22 years)
- "tow ard th Su" (toward the Sun)
- "h's cir umfe" (Earth's circumference)
- "NASA 's m issio ns Mars" (NASA's missions to Mars)

**Key Finding**: Font attack introduces OCR/reading errors that are visible in verbatim output.

#### Dual Layer PDF
- **File**: `astronomy_graduate_doc_02_dual_layer_final.pdf`
- **Detection Rate**: 66.67% (8/12)
- **MCQ**: 100% (5/5) ✓
- **True/False**: 20% (1/5) ✓
- **Long-form**: 100% (2/2) ✓

**Verbatim Reading Observations**:
- AI reading clean text: "common feature" ✓
- "Mercury" ✓
- "microscope" ✓
- "22 years" ✓
- All text appears correctly read

**Key Finding**: Dual layer attack does not show visible OCR errors in verbatim output.

### Comparison

| Metric | Font Attack | Dual Layer | Difference |
|--------|-------------|------------|------------|
| Overall Detection | 58.33% | 66.67% | +8.34% |
| MCQ Detection | 100% | 100% | Same |
| TF Detection | 0% | 20% | +20% |
| Long-form Detection | 100% | 100% | Same |

**Conclusion**: Dual Layer performs better overall, especially on True/False questions.

## API Usage

### v1/files Endpoint

The system uses OpenAI's v1/files endpoint for PDF upload:

1. **Upload**:
   ```python
   file_response = client.files.create(
       file=pdf_file,
       purpose="user_data"
   )
   file_id = file_response.id
   ```

2. **Wait for Processing**:
   ```python
   while file_status.status != "processed":
       file_status = client.files.retrieve(file_id)
       time.sleep(2)
   ```

3. **Use in Chat Completions**:
   ```python
   response = client.chat.completions.create(
       model="gpt-4o",
       messages=[{
           "role": "user",
           "content": [
               {
                   "type": "file",
                   "file": {
                       "file_id": file_id
                   }
               },
               {
                   "type": "text",
                   "text": prompt
               }
           ]
       }]
   )
   ```

4. **Cleanup**:
   ```python
   client.files.delete(file_id)
   ```

### Important Notes

- **File Type**: Must use `"type": "file"` (not "input_file")
- **File Parameter**: Must be object `{"file_id": "file-xxx"}` (not string)
- **Purpose**: Use `"user_data"` for user-uploaded files
- **Processing**: Files must be processed before use (status="processed")

## Output Files

### Detection System Outputs

Located in `output_detection/<timestamp>/`:

1. **`*_responses.json`**: Raw AI responses with metadata
   - Contains: question_number, ai_answer, gold_answer, target_wrong_answer, raw_response
   - Used for: Response analysis, debugging

2. **`detection_results.json`**: Structured detection results
   - Contains: detected, refused, reason, match_confidence for each question
   - Used for: Metrics calculation, reporting

3. **`detection_metrics.json`**: Aggregated metrics
   - Contains: Overall detection rate, refusal rate, breakdown by question type
   - Used for: Performance evaluation

4. **`detection_report.txt`**: Human-readable report
   - Contains: Summary, breakdown, sample results
   - Used for: Quick inspection

### Test Script Outputs

Located in `test_verbatim_outputs/`:

- **`*_verbatim_*.json`**: Full test outputs with verbatim question reading
  - Contains: prompt, response, usage, metadata
  - Used for: Inspecting how attacks affect text reading

## Differences Between Test Script and Detection System

### Why Outputs Differ

The test script and detection system may show different AI responses because:

1. **Non-deterministic AI**: Even with temperature=0, there can be variability
2. **Different Prompts**: Test script uses explicit "verbatim" instruction
3. **Timing**: Different API calls may get different responses
4. **Model Versioning**: Different model versions may behave differently

### Example Differences Observed

**Question 1**:
- Test Script: "(c) A source of organic molecules"
- Detection System: "A: The ability to breathe oxygen"
- **Different answers** - shows AI variability

**Question 5**:
- Test Script: "(c) 1609 (microscope)"
- Detection System: "C: 1609 (telescope)"
- **Different** - test says "microscope", detection says "telescope"

**Question 7**:
- Test Script: "False (The solar cycle is approximately 11 years.)"
- Detection System: "True"
- **Different answers**

### What This Means

The detection system correctly captures what the AI actually said. The inconsistency is in the AI's responses, not in the parsing. This highlights the importance of:
- Using temperature=0 for deterministic outputs
- Running multiple trials for statistical significance
- Documenting model versions used

## Running Full Evaluation

### Using Detection System

```bash
# Test single PDF directory
python3 -m src.detection.test --pdfs output_attacked_pdfs/.../font_attack --model gpt-4o

# Limit number of PDFs
python3 -m src.detection.test --pdfs output_attacked_pdfs/.../font_attack --model gpt-4o --limit 1

# Custom output directory
python3 -m src.detection.test --pdfs output_attacked_pdfs/.../font_attack --model gpt-4o --output custom_output
```

### Using Test Scripts

```bash
# Basic test
python3 test_pdf_upload.py document.pdf --all

# Verbatim reading test
python3 test_verbatim_questions.py document.pdf
```

## Future Improvements

### Planned Changes

1. **Replace Regex with Pydantic + LLM Judge**:
   - Current: Regex-based parsing in `_parse_response_by_question()`
   - Planned: Pydantic models + structured output parsing
   - Benefit: More robust, handles edge cases better

2. **Remove Question Formatting**:
   - Current: Some question formatting may still exist
   - Planned: Only send PDF, no question text at all
   - Benefit: Pure evaluation, no hints to AI

3. **Deterministic Outputs**:
   - Current: May have some variability
   - Planned: Ensure temperature=0, seed if available
   - Benefit: Reproducible results

4. **Better Error Handling**:
   - Current: Basic error handling
   - Planned: Retry logic, fallback strategies
   - Benefit: More robust evaluation

## Troubleshooting

### Common Issues

1. **API Key Not Found**:
   - Set `OPENAI_API_KEY` environment variable
   - Or configure in `config/config.yaml`

2. **File Upload Fails**:
   - Check file size (must be < 50MB)
   - Verify file is valid PDF
   - Check API quota/limits

3. **File Processing Timeout**:
   - Increase `max_wait` in code
   - Check file complexity
   - Verify API status

4. **Different Responses**:
   - Expected: AI can give different answers
   - Solution: Run multiple trials, use temperature=0
   - Document model version used

## References

- OpenAI v1/files API: https://platform.openai.com/docs/guides/pdf-files
- Detection System: `src/detection/`
- Test Scripts: `test_pdf_upload.py`, `test_verbatim_questions.py`
- Outputs: `output_detection/`, `test_verbatim_outputs/`

## Version History

- **2025-12-23**: Initial documentation
  - Added test scripts
  - Documented evaluation methodology
  - Recorded test results for font attack and dual layer
  - Documented verbatim reading findings

