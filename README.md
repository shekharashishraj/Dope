# IntegrityShield Perturbation Generation Pipeline

This pipeline processes JSON question files from academic assessments, generates imperceptible document-layer perturbations using OpenAI GPT-4o, and saves the results for academic integrity protection.

## Overview

The IntegrityShield framework fortifies PDF-based assessments through imperceptible document-layer perturbations that exploit the render–parse gap: what humans see differs from what MLLMs process. This pipeline generates perturbation mappings for Multiple Choice (MCQ), True/False (TF), and Long-form (LONG) questions.

## Features

- **Batch Processing**: Process multiple documents per batch for efficiency
- **Resume Support**: Skip already processed files (check if output exists)
- **Error Handling**: Robust error handling with detailed logging
- **Progress Tracking**: Console output showing progress through documents
- **Flexible Prompts**: Easy-to-modify prompt templates for each question type
- **Structure Preservation**: Maintains exact folder hierarchy with `_perturbation` suffix
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

The pipeline will:
1. Discover all JSON files in the `output/` directory
2. Load corresponding LaTeX files
3. Extract LaTeX stem text for each question
4. Generate 3 perturbation mappings per question using GPT-4o
5. Save outputs with perturbations array added to each question

### Injection Suite

Once perturbations exist, you can generate manipulated LaTeX/PDF outputs using
the injection harness (e.g., ICW, dual-layer, font attack). The quickest way to
exercise every injector on sample docs is the tester script:

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
  timeout: 60
  temperature: 0.7

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
│   ├── openai_client.py      # OpenAI API integration with batching
│   ├── file_handler.py       # JSON I/O and folder structure management
│   ├── latex_parser.py       # LaTeX parsing utilities
│   └── config.py             # Configuration management
├── prompts/
│   ├── __init__.py
│   ├── mcq_prompt.py         # MCQ perturbation prompt template
│   ├── tf_prompt.py          # True/False perturbation prompt template
│   └── long_prompt.py        # Long-form perturbation prompt template
├── config/
│   └── config.yaml           # Configuration file
├── output/                   # Input directory (JSON files)
├── docs.md                   # Font attack implementation notes
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
└── README.md                 # This file
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

Output files are saved to `{subject}/{level}/JSON_output_perturbation/` with the suffix `_perturbation.json`.

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

## Notes

- PDF injection phase (hidden text insertion) is separate and not included in this pipeline
- Batch strategy: Keep all questions from same document together when batching
- Each question generates exactly 3 mappings (k=3) by default
- LaTeX parsing matches question numbers from JSON to `\item` entries in LaTeX files
- The pipeline uses structured output (JSON mode) for reliable parsing

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
- To disable resume mode permanently, set `resume: false` in `config/config.yaml`

## License

[Add your license here]
