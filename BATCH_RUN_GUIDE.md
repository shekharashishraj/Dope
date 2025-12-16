# Batch Run Guide - Asynchronous Processing

## Quick Start

**Submit and Exit (No Waiting):**
```bash
python -m src.processor --mode batch --limit 2
```
Script exits immediately - batches process in background (1-24 hours)

**Check Status Later:**
```bash
python -m src.batch_retriever --list
python -m src.batch_retriever --batch-id <BATCH_ID> --check-only
```

**Retrieve Results When Ready:**
```bash
python -m src.batch_retriever --batch-id <BATCH_ID>
```

---

## Overview

Batch mode uses OpenAI's Batch API for asynchronous processing. This allows you to:
- **Submit jobs and exit immediately** (no waiting)
- **Save 50% on API costs**
- **Process large volumes** without rate limit issues
- **Check status and retrieve results later**

## Running Batch Mode

### Submit Batches (No Waiting)

```bash
# Process all documents in batch mode
python -m src.processor --mode batch

# Process specific number of documents
python -m src.processor --mode batch --limit 2

# Force reprocessing (even if outputs exist)
python -m src.processor --mode batch --force
```

**What happens:**
1. Script creates batch files (JSONL format)
2. Uploads to OpenAI Batch API
3. Gets batch IDs
4. Saves batch info to `output_perturbation/TIMESTAMP/subject/level/question_paper_name/batch_info.json`
5. **Script exits immediately** - no waiting!

**Output Structure:**
```
output_perturbation/
  └── YYYYMMDD_HHMMSS/              # Timestamp of batch run
      └── cybersecurity/
          └── undergraduate/
              └── cybersecurity_undergraduate_doc_01/
                  ├── batch_files/
                  │   ├── cybersecurity_undergraduate_doc_01_batch.jsonl
                  │   └── batch_info.json
                  └── (results will be saved here when retrieved)
```

## Retrieving Batch Results

### Step 1: List All Batches

Check all submitted batches and their status:

```bash
python -m src.batch_retriever --list
```

**Output shows:**
- Batch ID
- Status (submitted, in_progress, completed, etc.)
- Submission time
- Document name

### Step 2: Check Batch Status

Check if a specific batch is ready:

```bash
python -m src.batch_retriever --batch-id <BATCH_ID> --check-only
```

**Example:**
```bash
python -m src.batch_retriever --batch-id batch_69410a03c5988190a4437055062771bc --check-only
```

**Status Values:**
- `validating` - Batch is being validated
- `in_progress` - Batch is being processed
- `finalizing` - Batch is almost done
- `completed` ✅ - **Ready to download!**
- `expired` - Took longer than 24 hours
- `cancelled` - Was cancelled
- `failed` - Processing failed

### Step 3: Retrieve Completed Results

When status is `completed`, download and process results:

```bash
python -m src.batch_retriever --batch-id <BATCH_ID>
```

**What this does:**
1. Downloads results from OpenAI
2. Parses JSONL response file
3. Merges perturbations into JSON structure
4. Saves final output: `output_perturbation/TIMESTAMP/subject/level/question_paper_name/cybersecurity_undergraduate_doc_01_perturbation.json`
5. Updates batch_info.json with completion status

## Finding Your Batch IDs

### Method 1: From batch_info.json

Each document has a `batch_info.json` file:

```bash
# View batch info
cat output_perturbation/20251216_002800/cybersecurity/undergraduate/cybersecurity_undergraduate_doc_01/batch_files/batch_info.json
```

### Method 2: List All Batches

```bash
python -m src.batch_retriever --list
```

## Complete Workflow Example

### Day 1: Submit Batches

```bash
# Submit 2 documents for batch processing
python -m src.processor --mode batch --limit 2

# Output:
# Batch submitted successfully! Batch ID: batch_abc123xyz
# Use 'python -m src.batch_retriever --batch-id batch_abc123xyz' to check status
```

**Script exits immediately** - you can close terminal, go home, etc.

### Day 1 (Later) or Day 2: Check Status

```bash
# List all batches
python -m src.batch_retriever --list

# Check specific batch
python -m src.batch_retriever --batch-id batch_abc123xyz --check-only
```

### When Completed: Retrieve Results

```bash
# Download and process results
python -m src.batch_retriever --batch-id batch_abc123xyz

# Output:
# Batch Status: completed
# Downloading results...
# Saved perturbed JSON to: output_perturbation/.../cybersecurity_undergraduate_doc_01_perturbation.json
```

## Batch Processing Timeline

- **Submission**: Instant (script exits immediately)
- **Processing**: Typically 1-24 hours (often completes in 1-3 hours)
- **Completion**: Guaranteed within 24 hours
- **Cost**: 50% cheaper than immediate mode

## Tips

1. **Submit before leaving**: Run batch mode at end of day, check next morning
2. **Check periodically**: Use `--check-only` to see status without downloading
3. **Multiple batches**: Each document gets its own batch ID
4. **Organized structure**: Results are saved in organized folders by timestamp/subject/level
5. **Resume support**: If batch fails, you can resubmit with `--force`

## Troubleshooting

### Batch Status is "expired"
- Batch took longer than 24 hours
- Check if any results were completed before expiration
- Resubmit if needed

### Batch Status is "failed"
- Check error details in batch_info.json
- Resubmit with `--force` flag

### Can't Find Batch ID
- Use `--list` to see all batches
- Check `batch_info.json` files in output_perturbation directories

## Comparison: Immediate vs Batch

| Feature | Immediate Mode | Batch Mode |
|---------|---------------|------------|
| **Wait Time** | Waits for results | Exits immediately |
| **Cost** | Standard pricing | 50% discount |
| **Speed** | Real-time | 1-24 hours |
| **Use Case** | Small batches, testing | Large volumes, production |
| **Command** | `--mode immediate` (default) | `--mode batch` |

## Quick Reference Commands

```bash
# Submit batches (no waiting)
python -m src.processor --mode batch --limit 2

# List all batches
python -m src.batch_retriever --list

# Check status
python -m src.batch_retriever --batch-id <BATCH_ID> --check-only

# Retrieve results
python -m src.batch_retriever --batch-id <BATCH_ID>
```
