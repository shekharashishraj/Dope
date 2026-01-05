#!/usr/bin/env python3
"""Reorganize prevention PDF outputs to include variant folders."""

import shutil
from pathlib import Path
from tqdm import tqdm


def reorganize_prevention_outputs(output_root: Path) -> None:
    """Reorganize from <ts>/<domain>/<Level>/<doc>/<method>/... to <ts>/<domain>/<Level>/<doc>/<variant>/<method>/..."""
    
    # Find all PDFs
    pdfs = list(output_root.rglob("*.pdf"))
    
    moved = 0
    skipped = 0
    
    with tqdm(total=len(pdfs), desc="Reorganizing", unit="pdf") as pbar:
        for pdf_path in pdfs:
            # Skip if already in variant folder structure
            parts = pdf_path.parts
            if len(parts) < 6:
                skipped += 1
                pbar.update(1)
                continue
            
            # Current: <output_root>/<ts>/<domain>/<Level>/<doc>/<method>/<filename>.pdf
            # Target: <output_root>/<ts>/<domain>/<Level>/<doc>/<variant>/<method>/<filename>.pdf
            
            # Extract parts
            # parts[0] = output_prevention_attacked_pdfs
            # parts[1] = timestamp
            # parts[2] = domain
            # parts[3] = Level
            # parts[4] = doc
            # parts[5] = method
            # parts[6] = filename.pdf
            
            if len(parts) < 7:
                skipped += 1
                pbar.update(1)
                continue
            
            timestamp = parts[1]
            domain = parts[2]
            level = parts[3]
            doc = parts[4]
            method = parts[5]
            filename = parts[6]
            
            # Extract variant from filename
            # ICW: <doc>_icw.pdf (no variant)
            # Others: <doc>_<variant>_<method>.pdf
            
            if method == "icw":
                # ICW has no variant, keep structure as is
                skipped += 1
                pbar.update(1)
                continue
            
            # Parse variant from filename
            # Format: <doc>_<variant>_<method>.pdf
            # Example: health_graduate_doc_01_gibberish_font_attack.pdf
            #          -> doc = health_graduate_doc_01, variant = gibberish, method = font_attack
            stem = filename.rsplit(".pdf", 1)[0]
            
            # Method names: dual_layer, font_attack, icw_dual_layer, icw_font_attack
            # Remove method suffix from stem
            method_suffix = f"_{method}"
            if not stem.endswith(method_suffix):
                skipped += 1
                pbar.update(1)
                continue
            
            # Remove method suffix to get: <doc>_<variant>
            doc_variant = stem[:-len(method_suffix)]
            
            # Check if it starts with doc name
            doc_prefix = f"{doc}_"
            if not doc_variant.startswith(doc_prefix):
                skipped += 1
                pbar.update(1)
                continue
            
            # Extract variant (everything after doc_)
            variant = doc_variant[len(doc_prefix):]
            
            if not variant:
                skipped += 1
                pbar.update(1)
                continue
            
            # Build new path
            new_path = output_root / timestamp / domain / level / doc / variant / method / filename
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            if pdf_path != new_path:
                shutil.move(str(pdf_path), str(new_path))
                moved += 1
            else:
                skipped += 1
            
            pbar.update(1)
    
    print(f"\nReorganization complete:")
    print(f"  Moved: {moved}")
    print(f"  Skipped: {skipped} (ICW or already correct)")


if __name__ == "__main__":
    import sys
    output_root = Path("output_prevention_attacked_pdfs")
    if len(sys.argv) > 1:
        output_root = Path(sys.argv[1])
    
    if not output_root.exists():
        print(f"Error: {output_root} does not exist")
        sys.exit(1)
    
    reorganize_prevention_outputs(output_root)
