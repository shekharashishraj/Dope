#!/usr/bin/env python3
"""Filter PDFs to select 1 document per domain-level combination."""
from pathlib import Path
import sys

def filter_one_per_domain_level(pdf_dir: Path) -> list[Path]:
    """
    Select 1 PDF per domain-level combination.
    Prefers doc_01 if available.
    
    Args:
        pdf_dir: Directory containing PDFs
        
    Returns:
        List of selected PDF paths
    """
    combinations = {}
    pdfs = list(pdf_dir.rglob("*.pdf"))
    
    for pdf in pdfs:
        # Extract domain and level from path
        # Structure: domain/level/docid_variant_method.pdf
        parts = pdf.parts
        if len(parts) >= 3:
            domain = parts[-3]  # e.g., "biology"
            level = parts[-2]  # e.g., "undergraduate" or "graduate"
            key = f"{domain}/{level}"
            if key not in combinations:
                combinations[key] = []
            combinations[key].append(pdf)
    
    # Select 1 PDF per combination (prefer doc_01)
    selected_pdfs = []
    for key in sorted(combinations.keys()):
        pdf_list = sorted(combinations[key])
        # Prefer doc_01
        doc01 = [p for p in pdf_list if "doc_01" in p.name]
        if doc01:
            selected = doc01[0]
        else:
            selected = pdf_list[0]
        selected_pdfs.append(selected)
    
    return selected_pdfs

if __name__ == "__main__":
    pdf_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output_prevention_attacked_pdfs/consolidated")
    selected = filter_one_per_domain_level(pdf_dir)
    
    print(f"Selected {len(selected)} PDFs from {len(list(pdf_dir.rglob('*.pdf')))} total")
    for pdf in selected:
        print(pdf)
