# Quick Reference: Injection System

## Key Features (2026-01-02)

✅ **Question-Level Substitutions** - Substitutions work in question stems  
✅ **Automatic Extraction** - Corrects wrong `latex_stem_text` from JSON  
✅ **Robust Parsing** - Handles nested LaTeX structures  
✅ **Option-Level Support** - Searches in options when not found in stem  

## Quick Commands

```bash
# Generate PDFs from perturbations
python -m src.pdf_generator --perturbation-folder output_perturbation/20260102_123536

# Test injectors
python3 test_injector_question_level.py

# Verify extraction
python3 -c "from src.latex_parser import parse_latex_questions; print(len(parse_latex_questions('output/machine_learning/graduate/latex_documents/machine_learning_graduate_doc_02.tex')))"
```

## What Was Fixed

1. **LaTeX Extraction** - Now correctly extracts all questions (20/20 tested)
2. **Question-Level Support** - Substitutions work in question stems
3. **Extraction Fallback** - Auto-corrects wrong JSON `latex_stem_text`

## Files to Know

- `src/injection/dual_layer_injector.py` - Main dual layer injection
- `src/injection/font_attack_injector.py` - Font attack injection
- `src/latex_parser.py` - LaTeX extraction (fixed)
- `INJECTION_GUIDE.md` - Detailed guide
- `PERTURBATION_ANALYSIS.md` - Analysis and fixes

## Common Issues

**Q: Substitutions not applied?**  
A: Check logs. Extraction fallback should handle most cases. Verify `original_substring` exists in text.

**Q: Wrong questions extracted?**  
A: Should be fixed. Extraction now handles nested structures correctly.

**Q: Option-level substitutions not working?**  
A: Logic is in place but may need refinement. Ensure `original_substring` matches exactly.

