# Changelog

## [Latest] - 2025-12-16

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
