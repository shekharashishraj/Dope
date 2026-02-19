#!/usr/bin/env python3
"""Test converting a single HTML file to PDF with proper canvas rendering."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

html_path = Path("html-pdfs-attacked/biology/graduate/image_canvas/exam_printsafe.html")
pdf_path = html_path.with_suffix('.pdf')

print(f"Converting {html_path} to {pdf_path}...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Load the HTML file
    file_url = html_path.resolve().as_uri()
    print(f"Loading {file_url}...")
    page.goto(file_url, wait_until='networkidle', timeout=60000)
    
    # Wait for page to fully load
    page.wait_for_load_state('networkidle')
    print("Page loaded")
    
    # Wait for MathJax
    try:
        print("Waiting for MathJax...")
        page.wait_for_function(
            'window.MathJax && window.MathJax.startup && window.MathJax.startup.document && window.MathJax.startup.document.state() === 0',
            timeout=20000
        )
        print("MathJax loaded")
    except:
        print("MathJax timeout, continuing...")
        page.wait_for_timeout(5000)
    
    # Check what functions are available
    functions = page.evaluate('''
        ({
            renderAllCanvases: typeof renderAllCanvases,
            renderPrintCanvases: typeof renderPrintCanvases,
            canvasCount: document.querySelectorAll("canvas").length
        })
    ''')
    print(f"Available functions: {functions}")
    
    # Trigger beforeprint event
    print("Triggering beforeprint event...")
    page.evaluate('window.dispatchEvent(new Event("beforeprint"))')
    page.wait_for_timeout(3000)
    
    # Check canvas count after beforeprint
    canvas_count = page.evaluate('document.querySelectorAll("canvas").length')
    print(f"Canvas count after beforeprint: {canvas_count}")
    
    # Also try calling renderAllCanvases directly
    if functions.get('renderAllCanvases') == 'function':
        print("Calling renderAllCanvases()...")
        page.evaluate('renderAllCanvases()')
        page.wait_for_timeout(2000)
        canvas_count = page.evaluate('document.querySelectorAll("canvas").length')
        print(f"Canvas count after renderAllCanvases: {canvas_count}")
    
    # Set print media
    print("Setting print media...")
    page.emulate_media(media='print')
    page.wait_for_timeout(2000)
    
    # Check if canvases are visible in print media
    visible_canvases = page.evaluate('''
        Array.from(document.querySelectorAll("canvas")).filter(c => {
            const style = window.getComputedStyle(c);
            return style.display !== 'none' && style.visibility !== 'hidden';
        }).length
    ''')
    print(f"Visible canvases in print media: {visible_canvases}")
    
    # Generate PDF
    print(f"Generating PDF to {pdf_path}...")
    page.pdf(
        path=str(pdf_path),
        format='A4',
        print_background=True,
        prefer_css_page_size=True,
        margin={'top': '0.5in', 'right': '0.5in', 'bottom': '0.5in', 'left': '0.5in'}
    )
    
    browser.close()
    print(f"✓ PDF generated: {pdf_path}")
