#!/usr/bin/env python3
"""Convert exam_printsafe.html files to PDFs using playwright (executes JavaScript)."""

import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from playwright.sync_api import sync_playwright

def convert_html_to_pdf(html_path: Path) -> tuple[Path, bool, str]:
    """
    Convert a single HTML file to PDF using playwright (executes JavaScript for canvas overlays).
    
    Args:
        html_path: Path to the HTML file
        
    Returns:
        Tuple of (pdf_path, success, error_message)
    """
    try:
        # Output PDF path (same directory, same name, .pdf extension)
        pdf_path = html_path.with_suffix('.pdf')
        
        # Convert HTML to PDF using playwright (executes JavaScript)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Load the HTML file (use file:// protocol for local files)
            file_url = html_path.resolve().as_uri()
            page.goto(file_url, wait_until='networkidle', timeout=60000)
            
            # Wait for page to fully load
            page.wait_for_load_state('networkidle')
            page.wait_for_load_state('domcontentloaded')
            
            # Wait for MathJax to render if present
            try:
                page.wait_for_function(
                    'window.MathJax && window.MathJax.startup && window.MathJax.startup.document && window.MathJax.startup.document.state() === 0',
                    timeout=20000
                )
            except:
                # If MathJax doesn't load, wait a bit more
                page.wait_for_timeout(5000)
            
            # Set print media FIRST (before triggering canvas creation)
            # This ensures @media print CSS rules are active
            page.emulate_media(media='print')
            page.wait_for_timeout(1000)
            
            # Call renderAllCanvases() to create the canvas overlays with perturbations
            # This function is globally accessible and creates canvases with wrong answers
            page.evaluate('''
                if (typeof renderAllCanvases === 'function') {
                    renderAllCanvases();
                }
            ''')
            
            # Wait for canvases to be created and rendered
            page.wait_for_timeout(3000)
            
            # Verify canvases exist and are visible in print media
            canvas_info = page.evaluate('''() => {
                return {
                    total: document.querySelectorAll("canvas").length,
                    visible: Array.from(document.querySelectorAll("canvas")).filter(c => {
                        const style = window.getComputedStyle(c);
                        return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                    }).length
                };
            }''')
            
            if canvas_info['total'] == 0:
                # Try one more time to create canvases
                page.evaluate('if (typeof renderAllCanvases === "function") renderAllCanvases();')
                page.wait_for_timeout(2000)
            
            # Generate PDF with print media (this triggers @media print CSS)
            # The CSS will show the canvas overlays with perturbations
            page.pdf(
                path=str(pdf_path),
                format='A4',
                print_background=True,
                prefer_css_page_size=True,
                margin={'top': '0.5in', 'right': '0.5in', 'bottom': '0.5in', 'left': '0.5in'}
            )
            
            browser.close()
        
        return (pdf_path, True, "")
    except Exception as e:
        return (html_path.with_suffix('.pdf'), False, str(e))


def main():
    """Main entry point."""
    base_dir = Path("html-pdfs-attacked")
    
    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        sys.exit(1)
    
    # Find all exam_printsafe.html files
    html_files = list(base_dir.rglob("exam_printsafe.html"))
    
    if not html_files:
        print("No exam_printsafe.html files found")
        sys.exit(1)
    
    print(f"Found {len(html_files)} exam_printsafe.html files to convert")
    
    # Convert with parallel processing (5 workers)
    success_count = 0
    error_count = 0
    errors = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        future_to_html = {executor.submit(convert_html_to_pdf, html_path): html_path 
                         for html_path in html_files}
        
        # Process with progress bar
        with tqdm(total=len(html_files), desc="Converting HTML to PDF", unit="file") as pbar:
            for future in as_completed(future_to_html):
                html_path = future_to_html[future]
                try:
                    pdf_path, success, error_msg = future.result()
                    
                    if success:
                        success_count += 1
                        pbar.set_postfix(success=success_count, errors=error_count)
                    else:
                        error_count += 1
                        errors.append((html_path, error_msg))
                        pbar.set_postfix(success=success_count, errors=error_count)
                        tqdm.write(f"✗ Error converting {html_path}: {error_msg[:80]}", file=sys.stderr)
                        
                except Exception as e:
                    error_count += 1
                    errors.append((html_path, str(e)))
                    pbar.set_postfix(success=success_count, errors=error_count)
                    tqdm.write(f"✗ Exception converting {html_path}: {str(e)[:80]}", file=sys.stderr)
                
                pbar.update(1)
    
    # Summary
    print(f"\n✓ Conversion complete!")
    print(f"  Success: {success_count}/{len(html_files)}")
    print(f"  Errors: {error_count}/{len(html_files)}")
    
    if errors:
        print(f"\nErrors:")
        for html_path, error_msg in errors[:10]:  # Show first 10 errors
            print(f"  {html_path}: {error_msg[:100]}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
