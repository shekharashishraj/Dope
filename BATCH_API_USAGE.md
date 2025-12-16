# OpenAI Batch API Usage Guide

## Quick Reference

### Submit Batches

Submit all documents for batch processing (50% cost reduction):
```bash
python -m src.processor --mode batch
```

Submit with limit (for testing):
```bash
python -m src.processor --mode batch --limit 5
```

### Check Batch Status

List all submitted batches:
```bash
python -m src.batch_retriever --list
```

Check status of a specific batch:
```bash
python -m src.batch_retriever --batch-id <batch_id> --check-only
```

### Retrieve Results

Download and process completed batch results:
```bash
python -m src.batch_retriever --batch-id <batch_id>
```

## How It Works

1. **Submission**: When using `--mode batch`, the system:
   - Groups all questions from each document into a single batch
   - Creates a JSONL file with all requests
   - Uploads to OpenAI Batch API
   - Stores batch ID in `batch_info.json` for later retrieval
   - Exits immediately (no waiting)

2. **Processing**: OpenAI processes batches asynchronously:
   - Completion typically within 24 hours (often much sooner)
   - Status can be checked anytime
   - 50% cost reduction compared to immediate mode

3. **Retrieval**: When batch is completed:
   - Run the retriever script with the batch ID
   - Results are automatically downloaded and parsed
   - Perturbations are merged back into JSON files
   - Final output files are saved

## Batch Info Storage

Batch information is stored in:
- `output/<domain>/<level>/JSON_output_perturbation/batch_info.json`

Each batch entry contains:
- Batch ID
- Original JSON file path
- Batch file path
- Submission timestamp
- Status (submitted/completed)
- Output path (when completed)

## Fallback Behavior

If batch API fails during submission, the system automatically:
- Falls back to immediate mode
- Processes the document synchronously
- Saves results normally

## Example Workflow

```bash
# 1. Submit batches
python -m src.processor --mode batch

# Output shows:
# Batch submitted successfully! Batch ID: batch_abc123xyz
# Use 'python -m src.batch_retriever --batch-id batch_abc123xyz' to check status

# 2. Later, check if ready
python -m src.batch_retriever --batch-id batch_abc123xyz --check-only

# 3. When completed, retrieve results
python -m src.batch_retriever --batch-id batch_abc123xyz
```

## Notes

- Batch files are stored in `output/.../batch_files/` directory
- Results are stored in `output/.../batch_results/` directory
- You can check batch status anytime without downloading
- Multiple batches can be submitted and retrieved independently
