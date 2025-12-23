# Detection Module

This module implements the 3-step detection system for IntegrityShield:

1. **Response Collection**: Uploads perturbed PDFs to OpenAI API and collects AI responses
2. **Signature Matching**: Matches AI responses against expected detection signatures
3. **Metrics Calculation**: Calculates detection rates, refusal rates, and generates reports

## Usage

### Basic Usage

```bash
python -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o
```

### Options

- `--pdfs`: Directory containing perturbed PDFs (default: `output_attacked_pdfs`)
- `--model`: OpenAI model to use (default: `gpt-4o`)
- `--limit`: Limit number of PDFs to test (for testing)
- `--config`: Path to config file (default: `config/config.yaml`)
- `--output`: Output directory (default: `output_detection/<timestamp>`)

### Example

```bash
# Test first 2 PDFs
python -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o --limit 2

# Test all PDFs with custom output directory
python -m src.detection.test --pdfs output_attacked_pdfs --model gpt-4o --output my_detection_results
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
- Uploads each PDF to OpenAI API
- Sends questions and collects AI responses
- Saves responses with metadata

### Step 2: Signature Matching
- For each question, compares AI answer to:
  - **MCQ**: Checks if wrong option was selected
  - **True/False**: Checks if answer was flipped
  - **Long-form**: Checks for deviation from gold answer
- Detects refusals (when AI refuses to answer)
- Calculates match confidence scores

### Step 3: Metrics Calculation
- Calculates overall detection rate
- Calculates refusal rate
- Breaks down metrics by question type
- Generates summary report

## Notes

- **Model Support**: Currently tested with `gpt-4o`. Other vision-capable models may work.
- **PDF Upload**: Uses OpenAI's file upload API. PDFs are uploaded, processed, then deleted after use.
- **Rate Limiting**: Respects OpenAI rate limits with automatic retries.
- **Error Handling**: Continues processing even if individual PDFs fail.

## Requirements

- OpenAI API key must be set in environment variable `OPENAI_API_KEY`
- Perturbed PDFs must have corresponding perturbation JSON files
- PDFs should be in the expected directory structure

