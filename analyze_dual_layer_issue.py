#!/usr/bin/env python3
"""Analyze dual layer issue - why questions appear unchanged."""

import json
from pathlib import Path

# Check the generation results
results_file = Path("output_attacked_pdfs/20251228_150333/generation_results.json")
pert_file = Path("output_perturbation/20251228_150034/sociology/graduate/sociology_graduate_doc_01/sociology_graduate_doc_01_perturbation.json")
tex_file = Path("output_attacked_pdfs/20251228_150333/sociology/Graduate/sociology_graduate_doc_01/dual_layer/sociology_graduate_doc_01_dual_layer.tex")

print("=" * 80)
print("DUAL LAYER ANALYSIS")
print("=" * 80)

# Load perturbation data
with open(pert_file, 'r') as f:
    pert_data = json.load(f)

# Load generation results
with open(results_file, 'r') as f:
    results = json.load(f)

doc_key = "sociology_graduate_doc_01_perturbation.json"
if doc_key in results:
    doc_results = results[doc_key]
    dual_layer_result = doc_results.get("methods", {}).get("dual_layer", {})
    
    print(f"\nDocument: {doc_key}")
    print(f"Dual layer success: {dual_layer_result.get('success', False)}")
    print(f"Replacements count: {dual_layer_result.get('metadata', {}).get('replacements_count', 0)}")
    print(f"Final replacements count: {dual_layer_result.get('metadata', {}).get('final_replacements_count', 'N/A')}")
    print(f"Dual layer applied: {dual_layer_result.get('dual_layer_applied', False)}")
    print(f"Overlay method: {dual_layer_result.get('overlay_method', 'N/A')}")
    print(f"Original PDF used: {dual_layer_result.get('original_pdf_used', 'N/A')}")
    
    if dual_layer_result.get('overlay_error'):
        print(f"⚠️  Overlay error: {dual_layer_result.get('overlay_error')}")
    
    # Check replacements
    replacements = dual_layer_result.get('metadata', {}).get('replacements', [])
    print(f"\nReplacements applied:")
    for i, rep in enumerate(replacements[:5], 1):
        print(f"  {i}. Q{rep.get('question_number')}: '{rep.get('original')}' → '{rep.get('replacement')}'")

# Check LaTeX file
if tex_file.exists():
    tex_content = tex_file.read_text(encoding='utf-8')
    
    # Count duallayerbox occurrences
    dl_count = tex_content.count('\\duallayerbox')
    print(f"\nLaTeX Analysis:")
    print(f"  \\duallayerbox occurrences: {dl_count}")
    
    # Check first few occurrences
    import re
    dl_matches = list(re.finditer(r'\\duallayerbox\{([^}]+)\}\{([^}]+)\}', tex_content))
    print(f"  Found {len(dl_matches)} duallayerbox macros")
    
    if dl_matches:
        print(f"\nFirst 5 duallayerbox macros:")
        for i, match in enumerate(dl_matches[:5], 1):
            original = match.group(1)
            replacement = match.group(2)
            print(f"  {i}. Original: '{original[:50]}...'")
            print(f"     Replacement: '{replacement[:50]}...'")
else:
    print(f"\n⚠️  LaTeX file not found: {tex_file}")

# Check if original PDF exists
print(f"\n" + "=" * 80)
print("ORIGINAL PDF SEARCH")
print("=" * 80)

# Try to find original PDF
possible_locations = [
    Path("output/sociology/graduate/pdf_documents/sociology_graduate_doc_01.pdf"),
    Path("output/sociology/graduate/latex_documents/sociology_graduate_doc_01.pdf"),
]

for loc in possible_locations:
    if loc.exists():
        print(f"✓ Found original PDF: {loc}")
        break
else:
    print("✗ Original PDF not found in common locations")
    print("  This means the overlay will use the compiled PDF as fallback")
    print("  Result: Replacement text will be visible (questions will look changed)")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

if dual_layer_result.get('dual_layer_applied'):
    if 'fallback' in str(dual_layer_result.get('original_pdf_used', '')):
        print("⚠️  ISSUE: Original PDF not found, using compiled PDF as fallback")
        print("   This means the overlay is covering replacement text with itself")
        print("   Result: Questions appear unchanged (which is actually correct for dual layer)")
        print("   But the text layer should have replacement text for LLMs")
    else:
        print("✓ Overlay applied successfully with original PDF")
        print("  Visual layer: Shows original text (correct)")
        print("  Text layer: Contains replacement text (for LLMs)")
else:
    print("✗ Overlay was not applied")
    if dual_layer_result.get('overlay_error'):
        print(f"   Error: {dual_layer_result.get('overlay_error')}")
    else:
        print("   Check logs for details")

