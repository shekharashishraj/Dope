# Quick Start: Testing PDF Attacks

## Quick Commands

### Test Single PDF (Answer All Questions)
```bash
python3 test_pdf_upload.py path/to/document.pdf --all
```

### Test with Verbatim Question Reading
```bash
python3 test_verbatim_questions.py path/to/document.pdf
```

### Run Full Detection Evaluation
```bash
python3 -m src.detection.test --pdfs output_attacked_pdfs/.../font_attack --model gpt-4o
```

## Test Results Location

- **Detection System Outputs**: `output_detection/<timestamp>/`
- **Verbatim Test Outputs**: `test_verbatim_outputs/`

## Key Findings

### Font Attack
- Detection Rate: **58.33%**
- Shows OCR errors in verbatim reading (e.g., "c mm fea ture" instead of "common feature")

### Dual Layer
- Detection Rate: **66.67%**
- Text reads cleanly (no visible OCR errors)

## Output Files

1. `*_responses.json` - Raw AI responses
2. `detection_results.json` - Detection results per question
3. `detection_metrics.json` - Aggregated metrics
4. `detection_report.txt` - Human-readable report
5. `*_verbatim_*.json` - Verbatim question reading results

## See Full Documentation

See `TESTING_DOCUMENTATION.md` for complete details.

