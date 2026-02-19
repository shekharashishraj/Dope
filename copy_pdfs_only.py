#!/usr/bin/env python3
"""Copy only exam_printsafe.pdf files to a new directory, preserving structure."""

import sys
import shutil
from pathlib import Path
from tqdm import tqdm

def main():
    """Main entry point."""
    source_dir = Path("html-pdfs-attacked")
    dest_dir = Path("html-pdfs-attacked-pdfs-only")
    
    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        sys.exit(1)
    
    # Find all exam_printsafe.pdf files
    pdf_files = list(source_dir.rglob("exam_printsafe.pdf"))
    
    if not pdf_files:
        print("No exam_printsafe.pdf files found")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} exam_printsafe.pdf files to copy")
    
    # Copy files preserving directory structure
    copied = 0
    errors = []
    
    with tqdm(total=len(pdf_files), desc="Copying PDFs", unit="file") as pbar:
        for pdf_file in pdf_files:
            try:
                # Get relative path from source directory
                rel_path = pdf_file.relative_to(source_dir)
                
                # Create destination path
                dest_path = dest_dir / rel_path
                
                # Create parent directories
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy the file
                shutil.copy2(pdf_file, dest_path)
                copied += 1
                
            except Exception as e:
                errors.append((pdf_file, str(e)))
                tqdm.write(f"✗ Error copying {pdf_file}: {str(e)[:80]}", file=sys.stderr)
            
            pbar.update(1)
    
    # Summary
    print(f"\n✓ Copy complete!")
    print(f"  Copied: {copied}/{len(pdf_files)}")
    print(f"  Errors: {len(errors)}/{len(pdf_files)}")
    print(f"  Destination: {dest_dir}")
    
    if errors:
        print(f"\nErrors:")
        for pdf_file, error_msg in errors[:10]:
            print(f"  {pdf_file}: {error_msg[:100]}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    return 0 if len(errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
