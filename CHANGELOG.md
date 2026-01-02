# Changelog

## [2026-01-02] - Injection System Improvements

### Fixed
- **LaTeX Extraction Function**: Fixed `extract_question_stem_from_latex()` to correctly handle nested enumerate environments
  - Now properly extracts all questions (tested: 20/20 for test documents)
  - Handles both MCQ (with nested enumerate) and TF (without nested enumerate) questions
  - Uses depth tracking to identify top-level question items vs nested option items
  - Previously was extracting option text instead of question stems

- **Perturbation Application**: Fixed issue where only 2 out of 20 questions had perturbations applied
  - Root cause: Incorrect `latex_stem_text` in JSON files
  - Solution: Automatic extraction fallback when JSON `latex_stem_text` doesn't match

### Added
- **Question-Level Substitution Support**: Injectors now handle substitutions in question stems
  - Substitutions can target any part of the question text, not just options
  - Works with both correct and incorrect `latex_stem_text` from JSON
  - Tested and verified: ✓ PASS

- **Automatic Extraction Fallback**: Injectors automatically extract correct `latex_stem_text` when JSON is wrong
  - First tries to use `latex_stem_text` from perturbation JSON
  - If not found, extracts from LaTeX file by question number
  - No manual fixes needed for incorrect JSON files
  - Tested and verified: ✓ PASS

- **Option-Level Substitution Support**: Added logic to search in options when substring not found in stem
  - Falls back to searching nested enumerate (options) section
  - Handles substitutions in answer options
  - Status: Logic implemented, may need refinement for edge cases

- **Enhanced Text Matching**: Improved substring matching with multiple fallback strategies
  - Exact match first
  - Normalized whitespace matching
  - Partial match fallback
  - Search in options if not found in stem

### Changed
- **Dual Layer Injector**: Enhanced to support question-level and option-level substitutions
- **Font Attack Injector**: Added extraction fallback mechanism
- **LaTeX Parser**: Completely rewritten extraction logic for robustness

### Documentation
- Created `INJECTION_GUIDE.md` - Comprehensive guide to injection methods and improvements
- Updated `PERTURBATION_ANALYSIS.md` - Documented fixes and solutions
- Updated `docs.md` - Added injection improvements section
- Created `INJECTOR_TESTING_REPORT.md` - Test results and status

### Testing
- Added `test_injector_question_level.py` - Test suite for question-level substitutions
- Verified extraction: 20/20 questions correctly extracted
- Verified question-level substitutions: ✓ PASS
- Verified extraction fallback: ✓ PASS

## [Latest] - 2025-12-22

### Added
- **Pydantic Implementation**:
  - Full type safety with Pydantic models for all data structures
  - Configuration models using `pydantic-settings` for environment variable support
  - Automatic validation for perturbations, questions, and documents
  - Type hints throughout the codebase for better IDE support

- **Log Probabilities Collection**:
  - Token-level log probabilities for each generated perturbation
  - Top-k alternative tokens with their probabilities (configurable, default: 5)
  - Organized storage by question type (MCQ, TF, LONG)
  - Saved in separate JSON files: `logprobs/<question_type>/<doc>_<type>_logprobs.json`

- **API Metadata Collection**:
  - Response IDs for tracking and reproducibility
  - Model version and system fingerprints
  - Finish reasons (stop, length, content_filter)
  - Detailed token usage (prompt, completion, total, cached)
  - Token breakdown by role (system vs user)

- **Research Metrics Computation**:
  - Automatic entropy calculation from log probabilities
  - Confidence scores (average log probability per token)
  - API statistics (truncation rates, filter rates, token efficiency)
  - Cost analysis (total cost, cost per perturbation, breakdown by question type)
  - Metrics organized by question type: `research_metrics/<question_type>/<doc>_<type>_metrics.json`

- **Enhanced Output Structure**:
  - Log probabilities organized by question type in separate folders
  - Research metrics organized by question type
  - Overall metrics file for each document
  - All metrics in JSON format for easy analysis

### Changed
- **Configuration System**:
  - Migrated from dictionary-based to Pydantic `BaseSettings` model
  - Added `logprobs` and `top_logprobs` configuration options
  - Environment variable support via `pydantic-settings`
  - YAML configuration loading with automatic validation

- **Data Models**:
  - All data structures now use Pydantic models
  - `PerturbationMapping` includes `logprobs` and `api_metadata` fields
  - `Question` uses `QuestionType` enum for type safety
  - `Document` model for structured document handling

- **Injection Methods**:
  - Fixed duplicate/overlapping replacements in font attack injector
  - Fixed duplicate/overlapping replacements in dual layer injector
  - Improved question stem matching to handle `\item` prefixes in LaTeX
  - Better handling of first question (starts with `\item 1.`)

### Fixed
- **Import Errors**: Fixed relative import issues in injection modules (`...models` → `..models`)
- **Duplicate Replacements**: Font attack and dual layer now prevent duplicate/overlapping replacements
- **Question Stem Matching**: Improved matching logic to handle LaTeX `\item` prefixes
- **First Question Handling**: Fixed issue where first question was skipped due to `\item 1.` format

### Technical Details

#### Pydantic Models Structure
- `src/models/config.py`: All configuration models (OpenAI, Processing, Retry, Logging, etc.)
- `src/models/perturbation.py`: PerturbationMapping, Question, Document, APIMetadata models
- `src/models/api.py`: BatchStatus, BatchRequest models
- `src/models/enums.py`: QuestionType enum

#### Research Metrics
- Entropy: H = -Σ p(x) * log(p(x)) computed from top logprobs
- Confidence: Average log probability per token
- Token efficiency: Tokens per perturbation
- Cost tracking: Detailed cost breakdown by question type

#### Output Files
```
output_perturbation/<timestamp>/<subject>/<level>/<doc>/
├── <doc>_perturbation.json          # Main file with all perturbations
├── research_metrics.json            # Overall metrics
├── logprobs/
│   ├── mcq/<doc>_mcq_logprobs.json
│   ├── tf/<doc>_tf_logprobs.json
│   └── long/<doc>_long_logprobs.json
└── research_metrics/
    ├── mcq/<doc>_mcq_metrics.json
    ├── tf/<doc>_tf_metrics.json
    └── long/<doc>_long_metrics.json
```

### Files Modified
- `requirements.txt`: Added `pydantic>=2.0.0`, `pydantic-settings>=2.0.0`, `numpy>=1.24.0`
- `src/models/`: New directory with all Pydantic models
- `src/config.py`: Replaced with Pydantic Config model
- `src/processor.py`: Updated to use Pydantic models, added research metrics computation
- `src/openai_client.py`: Added logprobs and API metadata extraction
- `src/validation.py`: New validation module using Pydantic models
- `src/injection/*.py`: Updated all injectors to use Pydantic models, fixed imports
- `src/batch_retriever.py`: Added logprobs and research metrics saving
- `config/config.yaml`: Added logprobs configuration

### Dependencies
- Added: `pydantic>=2.0.0` for data validation
- Added: `pydantic-settings>=2.0.0` for configuration management
- Added: `numpy>=1.24.0` for research metrics computation

## [Previous] - 2025-12-16

### Added
- **Organized Output Structure**: 
  - Perturbation outputs: `output_perturbation/<timestamp>/<subject>/<level>/<question_paper_name>/`
  - PDF outputs: `output_attacked_pdfs/<timestamp>/<subject>/<level>/<question_paper_name>/<method>/`
  - Shared timestamp per run for easy tracking

- **PDF Generator Script** (`src/pdf_generator.py`):
  - Command-line tool to generate attacked PDFs from perturbation JSON files
  - Recursive search for perturbation files
  - Support for all injection methods (ICW, dual_layer, font_attack, hybrids)
  - Organized output structure matching perturbation structure
  - Detailed logging with MST timestamps

- **Enhanced Logging System**:
  - Complete prompts logged at DEBUG level (saved to file)
  - Complete API responses logged at DEBUG level (saved to file)
  - Token usage and cost estimates for all API calls
  - Detailed timing breakdowns for all operations
  - All timestamps in Mountain Standard Time (MST)
  - Separate log files for different operations:
    - `logs/perturbation_YYYYMMDD_HHMMSS.log`
    - `logs/batch_retrieval_YYYYMMDD_HHMMSS.log`
    - `logs/pdf_generation_YYYYMMDD_HHMMSS.log`

- **Batch API Integration**:
  - Full support for OpenAI Batch API (asynchronous processing)
  - 50% cost reduction compared to immediate mode
  - Submit and exit immediately (no waiting)
  - Batch retrieval script (`src/batch_retriever.py`) with detailed logging
  - Automatic fallback to immediate mode if batch fails

- **Documentation**:
  - `BATCH_RUN_GUIDE.md`: Comprehensive guide for batch API usage
  - `QUICK_BATCH_REFERENCE.txt`: Quick reference cheat sheet
  - Updated README with all new features and usage examples

### Changed
- **Configuration**:
  - API timeout increased from 60 to 120 seconds
  - Temperature changed from 0.7 to 0.5 for more consistent results

- **Dual-Layer Injector**:
  - Fixed overlapping replacements issue
  - Now uses only the first perturbation per question (instead of all k=3)
  - Prevents malformed LaTeX from multiple overlapping `\duallayerbox` macros

- **ICW Injector Logic**:
  - LONG questions: Uses `replacement_substring` (actual text)
  - MCQ/TF questions: Uses `target_wrong_answer` first, falls back to `replacement_substring`
  - Applied to both standalone ICW and hybrid injectors (ICW+DualLayer, ICW+FontAttack)

- **Output Structure**:
  - Both immediate and batch modes now use organized timestamp-based structure
  - Consistent organization across all output types

### Fixed
- **Logging Error**: Fixed `TypeError` in PDF generator when using `end=""` parameter with logger
- **LaTeX Compilation**: Fixed malformed LaTeX in dual-layer injector causing compilation errors
- **Font Cleanup**: Fonts are now properly cleaned up after successful PDF compilation
- **Variable Scope**: Fixed `NameError` for `force` parameter in `process_document`

### Technical Details

#### Logging Enhancements
- All API calls log complete prompts and responses at DEBUG level
- Token usage and estimated costs logged for every API call
- Processing times broken down by stage (load, prompt prep, API, merge, save)
- Summary statistics with total timing and counts

#### Batch API Workflow
1. Create JSONL batch file with all questions from a document
2. Upload to OpenAI Batch API
3. Script exits immediately after submission
4. Use `batch_retriever.py` to check status and retrieve results later
5. Results automatically merged back into JSON structure

#### PDF Generation Workflow
1. Point to perturbation folder (searches recursively)
2. Extract metadata (subject, level, document name) from JSON or path
3. Apply injection methods (ICW, dual_layer, font_attack, or hybrids)
4. Save to organized structure matching perturbation structure
5. Log all operations with detailed timing and results

### Files Modified
- `src/processor.py`: Added organized output structure, enhanced logging, batch mode support
- `src/openai_client.py`: Added batch API methods, enhanced logging with complete prompts/responses
- `src/batch_retriever.py`: Enhanced with MST logging, detailed timing, complete response logging
- `src/pdf_generator.py`: New file - PDF generation script with organized output
- `src/injection/orchestrator.py`: Added font cleanup after PDF compilation
- `src/injection/dual_layer_injector.py`: Fixed to use only first perturbation per question
- `src/injection/icw_injector.py`: Updated logic for LONG vs MCQ/TF question types
- `config/config.yaml`: Updated timeout and temperature values
- `requirements.txt`: Added `pytz` for timezone support
- `README.md`: Comprehensive updates with all new features
- `BATCH_RUN_GUIDE.md`: New comprehensive guide
- `QUICK_BATCH_REFERENCE.txt`: New quick reference

### Dependencies
- Added: `pytz>=2023.3` for MST timezone support
