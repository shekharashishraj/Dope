#!/usr/bin/env python3
"""
Apply print occlusion layer to image/canvas attacked HTML.
Ensures perturbed text is painted in PDF text layer while visually showing original question via opaque canvas overlay.
"""

import argparse
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup


def setup_logging(log_dir="logs"):
    """Setup logging to file with timestamp."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"03d_print_occlusion_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file


def inject_print_css(soup: BeautifulSoup):
    """Inject print media CSS into <head>."""
    head = soup.find('head')
    if not head:
        head = soup.new_tag('head')
        if soup.html:
            soup.html.insert(0, head)
        else:
            logging.error("No <html> tag found, cannot inject CSS")
            return False
    
    # Remove existing print occlusion CSS if present
    existing_css = soup.find(id="print-occlusion-css")
    if existing_css:
        existing_css.decompose()
        logging.info("Removed existing print-occlusion-css")
    
    # Create CSS content
    css_content = """/* ===== Print Occlusion Layer (Injected by 03d) ===== */

/* Screen: hide print canvases */
.print-occlusion-canvas {
  display: none !important;
}

/* Print: ensure perturbed text is painted */
@media print {
  .question-to-render {
    color: #222 !important;
    -webkit-text-fill-color: #222 !important;
    opacity: 1 !important;
    text-shadow: none !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .print-occlusion-canvas {
    display: block !important;
    position: absolute !important;
    z-index: 99999 !important;
    pointer-events: none !important;
  }
}
"""
    
    # Create and inject style tag
    style_tag = soup.new_tag('style', id="print-occlusion-css")
    style_tag.string = css_content
    head.append(style_tag)
    
    css_length = len(css_content)
    logging.info(f"Injected print occlusion CSS ({css_length} bytes)")
    logging.debug(f"CSS content (first 200 chars): {css_content[:200]}...")
    
    return True


def inject_print_js(soup: BeautifulSoup):
    """Inject print-only JavaScript before </body>."""
    body = soup.find('body')
    if not body:
        logging.error("No <body> tag found, cannot inject JavaScript")
        return False
    
    # Remove existing print occlusion JS if present
    existing_js = soup.find(id="print-occlusion-js")
    if existing_js:
        existing_js.decompose()
        logging.info("Removed existing print-occlusion-js")
    
    # Create JavaScript content
    js_content = r"""/* ===== Print Occlusion Layer (Injected by 03d) ===== */
(function() {
    // Helper: decode HTML entities (reuse from 03c if available)
    function decodeHtmlEntities(text) {
        if (typeof window.decodeHtmlEntities === 'function') {
            return window.decodeHtmlEntities(text);
        }
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = text;
        return tempDiv.textContent || tempDiv.innerText || text;
    }

    function getCardContainer(el) {
        return el.closest('.question-card') || el.parentElement;
    }

    function getTextForOverlay(el) {
        const originalText = (el.dataset.originalText || '').trim();
        if (!originalText) return null;

        // Replicate 03c's exact pipeline
        const decodedText = decodeHtmlEntities(originalText);
        
        let textAfterDelimiterStripping = decodedText;
        if (typeof stripLatexDelimiters === 'function') {
            textAfterDelimiterStripping = stripLatexDelimiters(decodedText);
        }
        
        // Convert LaTeX to plain text (same as 03c)
        let textForCanvas;
        try {
            if (typeof convertLatexToPlainText === 'function') {
                textForCanvas = convertLatexToPlainText(textAfterDelimiterStripping);
                if (!textForCanvas || textForCanvas.trim() === '') {
                    textForCanvas = textAfterDelimiterStripping;
                }
            } else {
                textForCanvas = textAfterDelimiterStripping;
            }
        } catch (error) {
            textForCanvas = textAfterDelimiterStripping;
        }
        
        return textForCanvas;
    }

    function removePrintCanvases() {
        document.querySelectorAll('canvas.print-occlusion-canvas').forEach(c => c.remove());
    }

    function renderPrintCanvases() {
        try {
            removePrintCanvases();

            document.querySelectorAll('.question-to-render').forEach(function(el) {
                const txt = getTextForOverlay(el);
                if (!txt) return;

                const card = getCardContainer(el);
                if (!card) return;

                const elRect = el.getBoundingClientRect();
                const cardRect = card.getBoundingClientRect();

                // Create canvas
                const canvas = document.createElement('canvas');
                canvas.className = 'print-occlusion-canvas';

                // Size canvas to match element exactly (robust padding for full coverage)
                const padding = 6; // Increased padding to ensure complete coverage of perturbed text
                const baseWidth = elRect.width;  // Use actual width, no minimum
                const baseHeight = elRect.height; // Use actual height, no minimum
                const width = Math.max(1, baseWidth + padding * 2); // Ensure at least 1px
                const height = Math.max(1, baseHeight + padding * 2); // Ensure at least 1px

                // High DPI for print clarity
                const dpr = window.devicePixelRatio || 2; // Use 2x for print
                canvas.width = Math.floor(width * dpr);
                canvas.height = Math.floor(height * dpr);

                // Position canvas relative to card (match 03c's approach)
                canvas.style.position = 'absolute';
                canvas.style.left = Math.floor((elRect.left - cardRect.left) - padding) + 'px';
                canvas.style.top = Math.floor((elRect.top - cardRect.top) - padding) + 'px';
                canvas.style.width = width + 'px';
                canvas.style.height = height + 'px';
                canvas.style.zIndex = '99999';
                canvas.style.pointerEvents = 'none';

                const ctx = canvas.getContext('2d');
                ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

                // OPAQUE BACKGROUND: critical for hiding perturbed text in print
                let bg = '#ffffff';
                try {
                    const cardStyle = window.getComputedStyle(card);
                    const bgColor = cardStyle.backgroundColor;
                    if (bgColor && 
                        bgColor !== 'rgba(0, 0, 0, 0)' && 
                        bgColor !== 'transparent' &&
                        !bgColor.match(/rgba?\([^)]*,\s*0\s*\)/)) {
                        bg = bgColor;
                    } else {
                        const bodyStyle = window.getComputedStyle(document.body);
                        if (bodyStyle.backgroundColor && 
                            bodyStyle.backgroundColor !== 'rgba(0, 0, 0, 0)' &&
                            bodyStyle.backgroundColor !== 'transparent') {
                            bg = bodyStyle.backgroundColor;
                        }
                    }
                } catch (e) {}

                ctx.fillStyle = bg;
                ctx.fillRect(0, 0, width, height);

                // Font match element (same as 03c)
                const cs = window.getComputedStyle(el);
                const fontSize = cs.fontSize || '16px';
                const fontFamily = cs.fontFamily || 'Arial, sans-serif';
                ctx.font = fontSize + ' ' + fontFamily;
                
                // Text color (same logic as 03c)
                let textColor = '#333';
                const parent = el.parentElement;
                const parentStyle = parent ? window.getComputedStyle(parent) : null;
                if (parentStyle && parentStyle.color && parentStyle.color !== 'transparent') {
                    textColor = parentStyle.color;
                } else {
                    const bodyStyle = window.getComputedStyle(document.body);
                    if (bodyStyle && bodyStyle.color && bodyStyle.color !== 'transparent') {
                        textColor = bodyStyle.color;
                    }
                }
                ctx.fillStyle = textColor;

                // Word wrap (adjusted for smaller canvas with minimal padding)
                const textPadding = 8; // Text inset from canvas edges (4px each side)
                const maxWidth = width - (textPadding * 2);
                const lineHeight = parseFloat(fontSize) * 1.2; // 03c uses 1.2
                let y = lineHeight; // 03c starts at lineHeight

                // Match 03c's line splitting (literal \n)
                const lines = String(txt).split('\\n');
                lines.forEach(function(line) {
                    const words = line.split(' ');
                    let currentLine = '';
                    
                    words.forEach(function(word) {
                        const testLine = currentLine + word + ' ';
                        const metrics = ctx.measureText(testLine);
                        
                        if (metrics.width > maxWidth && currentLine !== '') {
                            ctx.fillText(currentLine, textPadding, y);
                            y += lineHeight;
                            currentLine = word + ' ';
                        } else {
                            currentLine = testLine;
                        }
                    });
                    
                    if (currentLine !== '') {
                        ctx.fillText(currentLine, textPadding, y);
                        y += lineHeight;
                    }
                });

                // Insert canvas before element (match 03c's approach)
                card.insertBefore(canvas, el);
            });
        } catch (error) {
            console.error('Error rendering print canvases:', error);
        }
    }

    // Print hooks
    window.addEventListener('beforeprint', function() {
        // Wait for MathJax if present (same as 03c)
        if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
            MathJax.startup.promise.then(function() {
                renderPrintCanvases();
            });
        } else {
            renderPrintCanvases();
        }
    });

    window.addEventListener('afterprint', function() {
        removePrintCanvases();
    });

})();
"""
    
    # Create and inject script tag
    script_tag = soup.new_tag('script', id="print-occlusion-js")
    script_tag.string = js_content
    body.append(script_tag)
    
    js_length = len(js_content)
    logging.info(f"Injected print occlusion JavaScript ({js_length} bytes)")
    logging.debug(f"JavaScript code (first 500 chars): {js_content[:500]}...")
    
    return True


def apply_print_occlusion_layer(input_html: Path, output_html: Path):
    """Main function to apply print occlusion layer."""
    log_file = setup_logging()
    logging.info("=" * 80)
    logging.info("Starting Print Occlusion Layer Application")
    logging.info(f"Input HTML: {input_html}")
    logging.info(f"Output HTML: {output_html}")
    logging.info("=" * 80)
    
    # Validate input file
    if not input_html.exists():
        logging.error(f"Input HTML file not found: {input_html}")
        sys.exit(1)
    
    # Load HTML
    try:
        with open(input_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        html_size = os.path.getsize(input_html)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Count question-to-render elements
        question_elements = soup.find_all(class_='question-to-render')
        logging.info(f"Input HTML loaded ({html_size} bytes), found {len(question_elements)} .question-to-render elements")
        
        if len(question_elements) == 0:
            logging.warning("No .question-to-render elements found. This script should be run after 03c_apply_image_canvas_attack.py")
    except Exception as e:
        logging.error(f"Error loading input HTML: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)
    
    # Validate HTML structure
    if not soup.find('head'):
        logging.warning("No <head> tag found, will create one")
    if not soup.find('body'):
        logging.error("No <body> tag found in HTML")
        sys.exit(1)
    
    # Inject CSS
    css_success = inject_print_css(soup)
    if not css_success:
        logging.error("Failed to inject print occlusion CSS")
        sys.exit(1)
    
    # Inject JavaScript
    js_success = inject_print_js(soup)
    if not js_success:
        logging.error("Failed to inject print occlusion JavaScript")
        sys.exit(1)
    
    # Create output directory if needed
    output_html.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output HTML
    try:
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        output_size = os.path.getsize(output_html)
        logging.info(f"Output HTML written successfully ({output_size} bytes)")
    except Exception as e:
        logging.error(f"Error writing output HTML: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)
    
    # Summary
    logging.info("=" * 80)
    logging.info("Print Occlusion Layer Application Complete")
    logging.info(f"Input HTML: {input_html} ({html_size} bytes)")
    logging.info(f"Output HTML: {output_html} ({output_size} bytes)")
    logging.info(f"Question elements processed: {len(question_elements)}")
    logging.info(f"CSS injection: {'Success' if css_success else 'Failed'}")
    logging.info(f"JavaScript injection: {'Success' if js_success else 'Failed'}")
    logging.info("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Apply print occlusion layer to image/canvas attacked HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/03d_apply_print_occlusion_layer.py \\
    --input-html out/attacked/Maths/image_canvas/exam.html \\
    --output-html out/attacked/Maths/image_canvas/exam_printsafe.html
        """
    )
    parser.add_argument(
        '--input-html',
        required=True,
        type=Path,
        help='Path to input HTML file (output from 03c_apply_image_canvas_attack.py)'
    )
    parser.add_argument(
        '--output-html',
        required=True,
        type=Path,
        help='Path to output HTML file with print occlusion layer'
    )
    
    args = parser.parse_args()
    
    apply_print_occlusion_layer(args.input_html, args.output_html)


if __name__ == "__main__":
    main()

