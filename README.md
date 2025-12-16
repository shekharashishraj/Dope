# IntegrityShield Perturbation Generation Pipeline

This pipeline processes JSON question files from academic assessments, generates imperceptible document-layer perturbations using OpenAI GPT-4o, and saves the results for academic integrity protection.

## Overview

The IntegrityShield framework fortifies PDF-based assessments through imperceptible document-layer perturbations that exploit the render–parse gap: what humans see differs from what MLLMs process. This pipeline generates perturbation mappings for Multiple Choice (MCQ), True/False (TF), and Long-form (LONG) questions.

## Features

- **Batch Processing**: Process multiple documents per batch for efficiency
- **Asynchronous Batch API**: Submit jobs and exit immediately, retrieve results later (50% cost savings)
- **Resume Support**: Skip already processed files (check if output exists)
- **Error Handling**: Robust error handling with detailed logging
- **Comprehensive Logging**: Complete prompts, responses, timing, and cost estimates (MST timezone)
- **Organized Output Structure**: Timestamp-based folder organization for easy tracking
- **Progress Tracking**: Console output showing progress through documents
- **Flexible Prompts**: Easy-to-modify prompt templates for each question type
- **PDF Generation**: Command-line tool to generate attacked PDFs from perturbations
- **Font Attack Injection**: Optional PDF manipulation step that keeps visuals
  intact while altering the parse layer through custom fonts

## Installation

1. Clone the repository or navigate to the project directory.

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. Configure settings (optional):
   - Edit `config/config.yaml` to adjust batch size, model, etc.

## Usage

### Basic Usage

Run the pipeline:
```bash
python -m src.processor
```

Or with a limit for testing (process only first 5 files):
```bash
python -m src.processor --limit 5
```

Or force reprocessing of all files (including already processed ones):
```bash
python -m src.processor --force
```

**Command-line Arguments:**
- `--limit N`: Limit the number of files to process (useful for testing). Example: `--limit 5`
- `--config PATH`: Path to configuration file (default: `config/config.yaml`)
- `--force` or `--no-resume`: Force reprocessing of all files, even if output already exists (overrides `resume: true` in config)
- `--mode {immediate,batch}`: Processing mode (default: `immediate`)
  - `immediate`: Synchronous API calls with immediate results
  - `batch`: Use OpenAI Batch API (50% cost reduction, up to 24h completion)

The pipeline will:
1. Discover all JSON files in the `output/` directory
2. Load corresponding LaTeX files
3. Extract LaTeX stem text for each question
4. Generate 3 perturbation mappings per question using GPT-4o
5. Save outputs with perturbations array added to each question
6. Create organized output structure: `output_perturbation/<timestamp>/<subject>/<level>/<question_paper_name>/`
7. Log all operations with detailed timing and MST timestamps to `logs/perturbation_YYYYMMDD_HHMMSS.log`

### Batch API Mode (Cost-Effective, Asynchronous)

For large-scale processing, use the Batch API mode which offers **50% cost reduction** and **no waiting**:

```bash
# Submit batches and exit immediately (no waiting)
python -m src.processor --mode batch

# Process specific number of documents
python -m src.processor --mode batch --limit 2
```

**How it works:**
- All questions from each document are grouped into a single batch
- Batch files are created and uploaded to OpenAI
- **The script exits immediately after submission** (no waiting!)
- Batches are processed asynchronously (completion within 24 hours, often 1-3 hours)
- Results are saved in organized structure: `output_perturbation/TIMESTAMP/subject/level/question_paper_name/`

**Retrieving Batch Results (Later):**

1. **List all submitted batches:**
   ```bash
   python -m src.batch_retriever --list
   ```

2. **Check batch status (without downloading):**
   ```bash
   python -m src.batch_retriever --batch-id <batch_id> --check-only
   ```

3. **Download and process completed batches:**
   ```bash
   python -m src.batch_retriever --batch-id <batch_id>
   ```

The retriever will:
- Check if the batch is completed
- Download results automatically
- Parse and merge perturbations back into JSON files
- Save the final output files in the organized structure

**Note:** 
- If batch API fails, the system automatically falls back to immediate mode
- See `BATCH_RUN_GUIDE.md` for detailed instructions and workflow examples

### Injection Suite (PDF Generation)

Once perturbations exist, you can generate manipulated LaTeX/PDF outputs using
the injection methods. There are two ways to do this:

#### Method 1: Organized PDF Generation (Recommended)

Generate PDFs with organized folder structure matching the perturbation structure:

```bash
# Generate PDFs from perturbation folder
python -m src.pdf_generator --perturbation-folder output_perturbation/20251216_003912

# Generate PDFs with specific methods only
python -m src.pdf_generator --perturbation-folder output_perturbation/20251216_003912 --methods icw dual_layer

# Limit number of documents (for testing)
python -m src.pdf_generator --perturbation-folder output_perturbation/20251216_003912 --limit 2

# Skip PDF compilation (only generate LaTeX)
python -m src.pdf_generator --perturbation-folder output_perturbation/20251216_003912 --no-pdf
```

**Output Structure:**
PDFs are saved in: `output_attacked_pdfs/<timestamp>/<subject>/<level>/<question_paper_name>/<method>/`

**Command-line Arguments:**
- `--perturbation-folder PATH`: Path to folder containing perturbation JSON files (required, searches recursively)
- `--methods METHOD [METHOD ...]`: Injection methods to apply (choices: `icw`, `dual_layer`, `font_attack`, `icw_dual_layer`, `icw_font_attack`). Default: all methods
- `--limit N`: Limit number of documents to process (for testing)
- `--output-dir PATH`: Base output directory (default: `output_attacked_pdfs`)
- `--no-pdf`: Skip PDF compilation (only generate LaTeX files)

**Logging:**
- All operations are logged to `logs/pdf_generation_YYYYMMDD_HHMMSS.log`
- Includes complete prompts, responses, timing, and compilation results
- All timestamps in Mountain Standard Time (MST)

#### Method 2: Legacy Injection Tester

For backward compatibility, you can still use the original injection tester:

```bash
python3 -m src.injection_tester
```

This will:
1. Locate perturbation JSON files under `output/<domain>/<level>/JSON_output_perturbation/`
2. For each configured method (ICW, dual_layer, font_attack, icw_dual_layer,
   icw_font_attack) build modified LaTeX files under
   `output/<domain>/<level>/injected_<method>/`
3. Compile PDFs (XeLaTeX required for font attack) and place logs alongside
   the outputs

To target a single JSON file/method use `InjectionOrchestrator` directly; see
`src/injection_tester.py` for reference.

### Configuration

Edit `config/config.yaml` to customize:

```yaml
openai:
  model: "gpt-4o"
  batch_size: 5  # Number of documents per batch
  max_retries: 3
  timeout: 120  # API call timeout in seconds
  temperature: 0.5

processing:
  input_dir: "output"
  output_suffix: "_perturbation"
  resume: true  # Skip already processed files
  mappings_per_question: 3  # Number of perturbation mappings per question
```

## Project Structure

```
IGSHIELD/
├── src/
│   ├── __init__.py
│   ├── processor.py          # Main processing pipeline
│   ├── openai_client.py     # OpenAI API integration (sync & batch)
│   ├── batch_retriever.py   # Batch API result retrieval tool
│   ├── pdf_generator.py     # PDF generation from perturbations
│   ├── file_handler.py       # JSON I/O and folder structure management
│   ├── latex_parser.py      # LaTeX parsing utilities
│   ├── config.py            # Configuration management
│   └── injection/           # PDF injection methods
│       ├── orchestrator.py  # Injection orchestration
│       ├── icw_injector.py  # In-Context Watermarking
│       ├── dual_layer_injector.py  # Dual-layer visual overlay
│       ├── font_attack_injector.py # Font-based attack
│       └── hybrid_injectors.py     # Combined methods
├── prompts/
│   ├── __init__.py
│   ├── mcq_prompt.py        # MCQ perturbation prompt template
│   ├── tf_prompt.py         # True/False perturbation prompt template
│   └── long_prompt.py       # Long-form perturbation prompt template
├── config/
│   └── config.yaml          # Configuration file
├── output/                  # Input directory (JSON files)
├── output_perturbation/     # Organized perturbation outputs
│   └── <timestamp>/
│       └── <subject>/
│           └── <level>/
│               └── <question_paper_name>/
├── output_attacked_pdfs/    # Organized PDF outputs
│   └── <timestamp>/
│       └── <subject>/
│           └── <level>/
│               └── <question_paper_name>/
│                   └── <method>/
├── logs/                    # Detailed operation logs
│   ├── perturbation_*.log   # Perturbation generation logs
│   ├── batch_retrieval_*.log # Batch retrieval logs
│   └── pdf_generation_*.log  # PDF generation logs
├── docs.md                  # Font attack implementation notes
├── BATCH_RUN_GUIDE.md       # Detailed batch API guide
├── QUICK_BATCH_REFERENCE.txt # Quick batch commands
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── README.md                # This file
```

## Input Format

The pipeline expects JSON files in the following structure:

```json
{
  "docid": "subject_level_doc_01",
  "questions": [
    {
      "question_number": 1,
      "question_type": "MCQ",
      "stem_text": "Question text here...",
      "options": {
        "A": "Option A",
        "B": "Option B"
      },
      "gold_answer": "A",
      ...
    }
  ],
  "file_paths": {
    "latex_file": "output/subject/level/latex_documents/file.tex"
  }
}
```

## Output Format

The pipeline adds a `perturbations` field to each question:

```json
{
  "question_number": 1,
  "perturbations": [
    {
      "question_index": 1,
      "latex_stem_text": "...",
      "original_substring": "...",
      "replacement_substring": "...",
      "start_pos": 0,
      "end_pos": 5,
      "target_wrong_answer": "B",
      "reasoning": "..."
    }
  ]
}
```

**Output Structure (Organized):**

Both immediate and batch modes now save outputs in an organized structure:

```
output_perturbation/
└── <timestamp>/              # Run timestamp (YYYYMMDD_HHMMSS)
    └── <subject>/            # e.g., "cybersecurity"
        └── <level>/          # e.g., "undergraduate", "graduate", "k-12"
            └── <question_paper_name>/  # e.g., "cybersecurity_undergraduate_doc_01"
                └── <doc>_perturbation.json
```

This structure makes it easy to:
- Track runs by timestamp
- Organize by subject and academic level
- Find specific question papers
- Compare results across different runs

## Architecture

The pipeline follows this flow:

1. **Discovery**: Scan `output/` directory for JSON files
2. **Batching**: Group documents into batches
3. **Processing**: For each batch:
   - Load JSON and LaTeX files
   - Extract LaTeX stems for each question
   - Format prompts based on question type
   - Send to OpenAI GPT-4o API
   - Parse perturbation mappings
   - Merge back into JSON structure
4. **Saving**: Save outputs to mirrored folder structure

## Font Attack Manipulation

Once perturbations exist, the `font_attack` injector in `src/injection` can
render deceptive PDFs that preserve the original look while changing the
copy/paste output. Highlights:

1. **Attack Planning** – `FontAttackInjector` finds each LaTeX span, builds a
   hidden-to-visual mapping (including per-word splitting when replacements span
   multiple words), and records metadata for reproducibility.
2. **Font Generation** – `FontBuilder` clones Roboto glyphs, supporting
   multi-character composites and zero-width glyphs, and writes them to
   `output/.../injected_font_attack/fonts_*` directories.
3. **Compilation** – Run XeLaTeX with the generated fonts:

   ```bash
   cd output/<domain>/<level>/injected_font_attack
   rm -rf fonts && cp -R fonts_1 fonts
   xelatex -interaction=nonstopmode <doc>_font_attack_1font.tex
   ```

4. **Validation** – Inspect the rendered PDF and confirm via `pdftotext` (or
   copy/paste) that the text layer now contains the replacement phrases.

See the top-level `docs.md` file for a deeper knowledge-transfer guide that
captures helper methods, troubleshooting tips, and future enhancements.

### Injection Outputs & Verification

- Modified LaTeX lives under `output/<domain>/<level>/injected_<method>/` with
  suffixes such as `_font_attack_1font.tex`.
- PDF compilation logs (`*_compile.log`) accompany the PDFs for quick debugging.
- Font attack runs also emit `fonts_<n>/` directories; copy the desired folder to
  `fonts/` before re-running XeLaTeX manually.
- Use `pdftotext` or copy/paste checks to ensure the rendered text differs from
  the parsed layer as expected.

## Logging

All operations are logged with detailed information:

### Log Files
- **Perturbation Generation**: `logs/perturbation_YYYYMMDD_HHMMSS.log`
- **Batch Retrieval**: `logs/batch_retrieval_YYYYMMDD_HHMMSS.log`
- **PDF Generation**: `logs/pdf_generation_YYYYMMDD_HHMMSS.log`

### Log Contents
- **INFO Level** (Console + File):
  - Prompt length and preview
  - API call timing and attempts
  - Token usage and cost estimates
  - Response preview
  - Processing time breakdowns
  - Summary statistics

- **DEBUG Level** (File Only):
  - Complete prompts (full text)
  - Complete API responses (full text)
  - Detailed perturbation data (JSON)
  - Detailed timing breakdowns

### Timezone
All timestamps are in **Mountain Standard Time (MST)** for consistency.

## Notes

- PDF injection phase (hidden text insertion) is separate and not included in this pipeline
- Batch strategy: Keep all questions from same document together when batching
- Each question generates exactly 3 mappings (k=3) by default
- LaTeX parsing matches question numbers from JSON to `\item` entries in LaTeX files
- The pipeline uses structured output (JSON mode) for reliable parsing
- **Dual-layer injector** uses only the first perturbation per question to avoid overlapping replacements
- **ICW injector** uses `replacement_substring` for LONG questions, `target_wrong_answer` (with fallback) for MCQ/TF

## Troubleshooting

### API Key Issues
- Ensure `OPENAI_API_KEY` is set in `.env` file
- Check that the API key is valid and has sufficient credits

### LaTeX Parsing Issues
- If LaTeX stems are not found, the pipeline falls back to `stem_text` from JSON
- Check that LaTeX file paths in JSON are correct
- Verify that question numbers match between JSON and LaTeX files

### Rate Limiting
- Reduce `batch_size` in config if hitting rate limits
- The pipeline includes automatic retry with exponential backoff

### Skipping Already Processed Files
- By default, the pipeline skips files that have already been processed (resume mode)
- To reprocess all files, use `--force` or `--no-resume` flag

## Additional Documentation

- `docs.md`: Font Attack Manipulation notes covering injector internals,
  compilation/testing instructions, operational tips, and ideas for future work.
- `BATCH_RUN_GUIDE.md`: Comprehensive guide for using the Batch API mode with
  step-by-step instructions, status values, troubleshooting, and examples.
- `QUICK_BATCH_REFERENCE.txt`: Quick reference cheat sheet for batch commands.
- To disable resume mode permanently, set `resume: false` in `config/config.yaml`

## Recent Updates

### Version Updates (Latest)
- **Organized Output Structure**: Both perturbation and PDF outputs now use timestamp-based organization
- **Enhanced Logging**: Complete prompts, responses, timing, and cost estimates with MST timestamps
- **PDF Generator Script**: New command-line tool (`pdf_generator.py`) for generating attacked PDFs
- **Batch API Integration**: Full support for asynchronous processing with 50% cost savings
- **Dual-Layer Fix**: Fixed overlapping replacements issue by using only first perturbation per question
- **ICW Logic**: Corrected to use `replacement_substring` for LONG questions
- **Increased Timeout**: API timeout increased to 120 seconds
- **Temperature Adjustment**: Default temperature set to 0.5 for more consistent results

## License

[Add your license here]
