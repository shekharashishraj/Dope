# Detection Module

This module implements the 3-step detection system for IntegrityShield:

1. **Response Collection**: Uploads perturbed PDFs to OpenAI API and collects AI responses
2. **Signature Matching**: Matches AI responses against expected detection signatures
3. **Metrics Calculation**: Calculates detection rates, refusal rates, and generates reports

## Usage

### Quick Start

```bash
# Basic: Test all PDFs with default settings
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o

# Quick test: Limit to 1 PDF
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o --limit 1
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--pdfs` | Directory containing perturbed PDFs | `output_attacked_pdfs` |
| `--model` | OpenAI model to use | `gpt-4o` |
| `--limit` | Limit number of PDFs to test (for testing) | None (all PDFs) |
| `--config` | Path to config file | `config/config.yaml` |
| `--output` | Output directory | `output_detection/<timestamp>` |

### Common Usage Examples

**Basic Testing:**
```bash
# Test all PDFs
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o

# Test with limit (quick test)
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o --limit 1

# Custom output directory
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o --output my_results
```

**Specific Attack Types:**
```bash
# Test only font attack PDFs
python3 -m src.detection.test --pdfs output_attacked_pdfs/20251222_224039/astronomy/Graduate/astronomy_graduate_doc_02/font_attack --model gpt-4o

# Test only dual layer PDFs
python3 -m src.detection.test --pdfs output_attacked_pdfs/20251222_224039/astronomy/Graduate/astronomy_graduate_doc_02/dual_layer --model gpt-4o
```

**Different Models:**
```bash
# GPT-4o (default, recommended for best results)
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o

# GPT-4 Turbo (alternative)
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4-turbo

# GPT-4o-mini (faster, cheaper, for testing)
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o-mini --limit 5
```

**Custom Configuration:**
```bash
# Use custom config file
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o --config config/custom.yaml

# Combine options
python3 -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o --limit 2 --output test_run_001
```

## Output Structure

```
output_detection/
└── <timestamp>/
    ├── <document_name>/
    │   ├── <doc>_responses.json      # Step 1: AI responses
    │   └── detection_results.json    # Step 2: Matched results
    ├── detection_metrics.json        # Step 3: Overall metrics
    └── detection_report.txt          # Human-readable report
```

## How It Works

### Step 1: Response Collection
- Finds perturbed PDFs and their corresponding perturbation JSON files
- Uploads each PDF to OpenAI API via v1/files endpoint
- Sends prompt: "Please read this document and answer ALL questions that appear in it. For each question, provide the question number and your answer."
- **NO question text sent** - only PDF file
- Parses responses using Pydantic + LLM judge with automatic fallback
- **LLM extracts option letters** for MCQ questions (e.g., "B" from "(b) Metasploit")
- Saves responses with metadata including parsing method used and extracted options

### Step 2: Signature Matching
- For each question, compares AI answer to:
  - **MCQ**: Uses LLM-extracted option letter to check if wrong option was selected
  - **True/False**: Checks if answer was flipped using LLM-extracted True/False value
  - **Long-form**: Checks for deviation from gold answer using word overlap analysis
- Detects refusals (when AI refuses to answer)
- Calculates match confidence scores
- **No regex/string matching** - all extraction done by LLM judge with Pydantic

### Step 3: Metrics Calculation
- Calculates overall detection rate
- Calculates refusal rate
- Breaks down metrics by question type (MCQ, TF, LONG)
- **Breaks down metrics by parsing method** (llm_judge, json_mode, regex)
- Generates summary report with all breakdowns

### Parsing Methods

The system uses multiple parsing methods with automatic fallback:

1. **LLM Judge (Primary)**: Uses Pydantic models with structured output API
   - Method: `client.beta.chat.completions.parse()` with `AIResponse` model
   - Returns: `"llm_judge"` parsing method
   - **Extracts option letters for MCQ questions** (e.g., "B" from "(b) Metasploit")
   - Most robust, handles edge cases best
   - **No regex or string matching** - all extraction done by LLM

2. **JSON Mode (Fallback 1)**: Uses JSON mode if structured output fails
   - Method: `client.chat.completions.create()` with `response_format={"type": "json_object"}`
   - Returns: `"json_mode"` parsing method
   - Also extracts option letters via LLM
   - Good fallback for structured parsing

3. **Regex (Fallback 2)**: Traditional regex parsing as last resort
   - Method: Pattern matching on response text
   - Returns: `"regex"` parsing method
   - Used only if both LLM methods fail
   - **Note**: Regex fallback cannot extract option letters (returns `null`)

All parsing methods are tracked and metrics are calculated separately for each method in `by_parsing_method` section of `detection_metrics.json`.

## Notes

- **Model Support**: Currently tested with `gpt-4o`. Other vision-capable models may work.
- **PDF Upload**: Uses OpenAI's file upload API. PDFs are uploaded, processed, then deleted after use.
- **Rate Limiting**: Respects OpenAI rate limits with automatic retries.
- **Error Handling**: Continues processing even if individual PDFs fail.
- **Parsing Robustness**: Automatic fallback ensures responses are always parsed, even if primary method fails.

## Requirements

- OpenAI API key must be set in environment variable `OPENAI_API_KEY`
- Perturbed PDFs must have corresponding perturbation JSON files
- PDFs should be in the expected directory structure

