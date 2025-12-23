#!/usr/bin/env python3
"""
Apply image/canvas attack to baseline HTML using perturbations.
Renders original question text as canvas (visible to humans) while keeping perturbed text in DOM (read by LLMs).
"""

import json
import sys
import os
import logging
import shutil
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Optional


def setup_logging(log_dir="logs"):
    """Setup logging to file with timestamp."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"03c_image_canvas_{timestamp}.log")
    
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


def load_perturbed_exam(perturbed_json: str) -> Dict:
    """Load perturbed exam JSON file."""
    logging.info(f"Loading perturbed exam JSON: {perturbed_json}")
    if not os.path.exists(perturbed_json):
        logging.error(f"Perturbed JSON file not found: {perturbed_json}")
        sys.exit(1)
    
    try:
        with open(perturbed_json, 'r', encoding='utf-8') as f:
            exam_data = json.load(f)
        
        file_size = os.path.getsize(perturbed_json)
        num_sections = len(exam_data.get('sections', []))
        total_questions = sum(len(s.get('questions', [])) for s in exam_data.get('sections', []))
        
        # Count questions with perturbations
        questions_with_perturbations = 0
        for section in exam_data.get('sections', []):
            for question in section.get('questions', []):
                if question.get('perturbations'):
                    questions_with_perturbations += 1
        
        logging.info(f"Successfully loaded perturbed exam data ({file_size} bytes)")
        logging.info(f"Number of sections: {num_sections}")
        logging.info(f"Total questions: {total_questions}")
        logging.info(f"Questions with perturbations: {questions_with_perturbations}")
        
        return exam_data
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in perturbed file: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading perturbed file: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)


def find_question_perturbations(exam_data: Dict, question_id: str) -> List[Dict]:
    """Get perturbations for a specific question."""
    for section in exam_data.get('sections', []):
        for question in section.get('questions', []):
            if question.get('id') == question_id:
                perturbations = question.get('perturbations', [])
                logging.debug(f"Question {question_id}: Found {len(perturbations)} perturbations")
                return perturbations
    
    logging.debug(f"Question {question_id}: No perturbations found")
    return []


def apply_perturbation_to_dom(text: str, mapping: Dict, question_id: str):
    """Replace DOM text with perturbed version."""
    original_substring = mapping.get('original_substring', '')
    replacement_substring = mapping.get('replacement_substring', '')
    start_pos = mapping.get('start_pos', -1)
    end_pos = mapping.get('end_pos', -1)
    
    # Normalize text and substrings to match format used during perturbation generation
    # This ensures positions calculated on normalized text match when applying
    text = ' '.join(text.split())
    original_substring = ' '.join(original_substring.split())
    replacement_substring = ' '.join(replacement_substring.split())
    
    if not original_substring or not replacement_substring:
        logging.warning(f"Question {question_id}: Invalid mapping (empty substring)")
        return text, False
    
    if start_pos < 0 or end_pos < 0 or start_pos >= end_pos:
        logging.warning(f"Question {question_id}: Invalid positions [{start_pos}, {end_pos})")
        return text, False
    
    # Validate that the substring at the position matches
    if start_pos + len(original_substring) > len(text):
        logging.warning(f"Question {question_id}: Position out of bounds. Text length: {len(text)}, "
                       f"expected end: {start_pos + len(original_substring)}")
        return text, False
    
    actual_substring = text[start_pos:start_pos + len(original_substring)]
    if actual_substring != original_substring:
        logging.warning(f"Question {question_id}: Substring mismatch at position {start_pos}. "
                       f"Expected: '{original_substring[:50]}...', "
                       f"Found: '{actual_substring[:50]}...'")
        return text, False
    
    # Perform replacement
    new_text = text[:start_pos] + replacement_substring + text[start_pos + len(original_substring):]
    
    logging.info(f"Question {question_id}: Replaced '{original_substring[:50]}...' with "
                f"'{replacement_substring[:50]}...' at position [{start_pos}, {start_pos + len(original_substring)})")
    logging.debug(f"Question {question_id}: Text before replacement: {text[:200]}...")
    logging.debug(f"Question {question_id}: Text after replacement: {new_text[:200]}...")
    
    return new_text, True


def inject_canvas_rendering_script(soup: BeautifulSoup):
    """Inject JavaScript that renders original text on canvas."""
    script_content = r"""
// Helper functions for text processing
function decodeHtmlEntities(text) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = text;
    return tempDiv.textContent || tempDiv.innerText || text;
}

// Strip LaTeX delimiters for canvas rendering
// Remove $...$, \(...\), \[...\], $$...$$ delimiters
function stripLatexDelimiters(text) {
    return text
        .replace(/\$\$([\s\S]+?)\$\$/g, '$1')          // Remove $$...$$
        .replace(/\$([\s\S]+?)\$/g, '$1')              // Remove $...$
        .replace(/\\\(([\s\S]+?)\\\)/g, '$1')          // Remove \( ... \)
        .replace(/\\\[([\s\S]+?)\\\]/g, '$1')           // Remove \[ ... \]
        .replace(/\\begin\{equation\}([\s\S]*?)\\end\{equation\}/g, '$1')  // Remove equation environments
        .replace(/\\begin\{align\}([\s\S]*?)\\end\{align\}/g, '$1');       // Remove align environments
}

// Convert LaTeX commands to plain text equivalents
function convertLatexToPlainText(text) {
            let result = text;
            
            // Convert fractions: numerator/denominator format
            // Handle nested braces by matching from innermost to outermost
            result = result.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, function(match, num, den) {
                // Recursively convert nested LaTeX in numerator and denominator
                const numPlain = convertLatexToPlainText(num);
                const denPlain = convertLatexToPlainText(den);
                return numPlain + '/' + denPlain;
            });
            
            // Convert escaped braces to regular braces
            result = result.replace(/\\\{/g, '{');
            result = result.replace(/\\\}/g, '}');
            
            // Convert other common LaTeX commands to plain text
            result = result.replace(/\\cdot/g, '·');           // cdot -> ·
            result = result.replace(/\\times/g, '×');          // times -> ×
            result = result.replace(/\\div/g, '÷');            // div -> ÷
            result = result.replace(/\\pm/g, '±');             // pm -> ±
            result = result.replace(/\\leq/g, '≤');            // leq -> ≤
            result = result.replace(/\\geq/g, '≥');            // geq -> ≥
            result = result.replace(/\\neq/g, '≠');            // neq -> ≠
            result = result.replace(/\\approx/g, '≈');          // approx -> ≈
            result = result.replace(/\\sqrt\{([^}]+)\}/g, '√($1)');  // sqrt -> √(x)
            result = result.replace(/\\sqrt\[([^\]]+)\]\{([^}]+)\}/g, '$1√($2)');  // sqrt with index -> n√(x)
            result = result.replace(/\\pi/g, 'π');             // pi -> π
            result = result.replace(/\\theta/g, 'θ');          // theta -> θ
            result = result.replace(/\\alpha/g, 'α');           // alpha -> α
            result = result.replace(/\\beta/g, 'β');            // beta -> β
            result = result.replace(/\\gamma/g, 'γ');           // gamma -> γ
            result = result.replace(/\\Delta/g, 'Δ');           // Delta -> Δ
            result = result.replace(/\\sum/g, 'Σ');             // sum -> Σ
            result = result.replace(/\\prod/g, 'Π');            // prod -> Π
            result = result.replace(/\\int/g, '∫');             // int -> ∫
            
            // Convert superscripts: x^2 format -> x² (simple cases)
            // Note: Complex superscripts may need special handling
            result = result.replace(/\^\{([^}]+)\}/g, function(match, exp) {
                // For simple numeric exponents, convert to superscript
                if (/^\d+$/.test(exp)) {
                    const superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', 
                                          '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'};
                    return exp.split('').map(function(d) { return superscripts[d] || d; }).join('');
                }
                return '^(' + exp + ')';
            });
            result = result.replace(/\^(\d)/g, function(match, exp) {
                const superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', 
                                      '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'};
                return superscripts[exp] || '^' + exp;
            });
            
            // Convert subscripts: x_2 format -> x₂ (simple cases)
            result = result.replace(/_\{([^}]+)\}/g, function(match, sub) {
                if (/^\d+$/.test(sub)) {
                    const subscripts = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', 
                                        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'};
                    return sub.split('').map(function(d) { return subscripts[d] || d; }).join('');
                }
                return '_(' + sub + ')';
            });
            result = result.replace(/_(\d)/g, function(match, sub) {
                const subscripts = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', 
                                    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'};
                return subscripts[sub] || '_' + sub;
            });
            
            return result;
        }
        
        // Main rendering function
        function renderAllCanvases() {
            document.querySelectorAll('.question-to-render').forEach(function(element) {
                const originalText = (element.dataset.originalText || '').trim();
                if (!originalText) {
                    console.warn('Element missing data-original-text attribute');
                    return;
                }
                
                const decodedText = decodeHtmlEntities(originalText);
                const textAfterDelimiterStripping = stripLatexDelimiters(decodedText);
                
                // Convert LaTeX to plain text with error handling
                let textForCanvas;
                try {
                    textForCanvas = convertLatexToPlainText(textAfterDelimiterStripping);
                    // Fallback to original if conversion returns empty or undefined
                    if (!textForCanvas || textForCanvas.trim() === '') {
                        textForCanvas = textAfterDelimiterStripping;
                    }
                } catch (error) {
                    console.warn('Error converting LaTeX to plain text:', error);
                    // Fallback to text after delimiter stripping
                    textForCanvas = textAfterDelimiterStripping;
                }
                
                // Create canvas element
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // Set canvas size to match element (with some padding)
                const rect = element.getBoundingClientRect();
                canvas.width = Math.max(rect.width, 800);
                canvas.height = Math.max(rect.height, 200);
                
                // Set font to match element's computed style
                const computedStyle = window.getComputedStyle(element);
                const fontSize = computedStyle.fontSize || '16px';
                const fontFamily = computedStyle.fontFamily || 'Arial, sans-serif';
                ctx.font = fontSize + ' ' + fontFamily;
                
                // Get color from parent element (not affected by transparent CSS)
                const parent = element.parentElement;
                const parentStyle = parent ? window.getComputedStyle(parent) : null;
                // Try to get color from parent, fallback to body, then default
                let textColor = '#333'; // Default fallback
                if (parentStyle && parentStyle.color && parentStyle.color !== 'transparent') {
                    textColor = parentStyle.color;
                } else {
                    // Fallback to body color or default
                    const bodyStyle = window.getComputedStyle(document.body);
                    if (bodyStyle && bodyStyle.color && bodyStyle.color !== 'transparent') {
                        textColor = bodyStyle.color;
                    }
                }
                ctx.fillStyle = textColor;
                
                // Draw original text on canvas
                // Split text into lines for better rendering
                const lines = textForCanvas.split('\\n');
                const lineHeight = parseFloat(fontSize) * 1.2;
                let y = lineHeight;
                
                lines.forEach(function(line) {
                    // Handle long lines by wrapping
                    const maxWidth = canvas.width - 40;
                    let words = line.split(' ');
                    let currentLine = '';
                    
                    words.forEach(function(word) {
                        const testLine = currentLine + word + ' ';
                        const metrics = ctx.measureText(testLine);
                        
                        if (metrics.width > maxWidth && currentLine !== '') {
                            ctx.fillText(currentLine, 20, y);
                            y += lineHeight;
                            currentLine = word + ' ';
                        } else {
                            currentLine = testLine;
                        }
                    });
                    
                    if (currentLine !== '') {
                        ctx.fillText(currentLine, 20, y);
                        y += lineHeight;
                    }
                });
                
                // Find parent question-card
                const parentCard = element.closest('.question-card');
                if (!parentCard) {
                    console.warn('Could not find parent question-card for canvas insertion');
                    return;
                }
                
                // Make parent card position relative to contain canvas overlay
                parentCard.style.position = 'relative';
                
                // Get the prompt element's position relative to the card
                const cardRect = parentCard.getBoundingClientRect();
                const elementRect = element.getBoundingClientRect();
                
                // Position canvas to overlay the prompt element
                canvas.style.position = 'absolute';
                canvas.style.left = (elementRect.left - cardRect.left) + 'px';
                canvas.style.top = (elementRect.top - cardRect.top) + 'px';
                canvas.style.zIndex = '10';
                canvas.style.pointerEvents = 'none';
                
                // Insert canvas as sibling before the prompt element in the card
                parentCard.insertBefore(canvas, element);
            });
        }
        
        // Wait for MathJax if present, then render
        window.addEventListener('load', function() {
            if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
                MathJax.startup.promise.then(function() {
                    renderAllCanvases();
                });
            } else {
                renderAllCanvases();
            }
        });
"""
    
    # Find or create script tag
    body = soup.find('body')
    if not body:
        logging.error("No <body> tag found in HTML")
        sys.exit(1)
    
    script_tag = soup.new_tag('script')
    script_tag.string = script_content
    body.append(script_tag)
    
    script_length = len(script_content)
    logging.info(f"Injected canvas rendering script ({script_length} bytes)")
    logging.debug(f"JavaScript code (first 500 chars): {script_content[:500]}...")
    
    return script_length


def apply_image_canvas_attack(baseline_html: str, perturbed_json: str, output_dir: str, subject_name: str):
    """Main function to apply image/canvas attack."""
    log_file = setup_logging()
    logging.info("=" * 80)
    logging.info("Starting Image/Canvas Attack Application")
    logging.info(f"Baseline HTML: {baseline_html}")
    logging.info(f"Perturbed JSON: {perturbed_json}")
    logging.info(f"Output directory: {output_dir}")
    logging.info(f"Subject name: {subject_name}")
    logging.info("=" * 80)
    
    # Load baseline HTML
    logging.info(f"Loading baseline HTML: {baseline_html}")
    if not os.path.exists(baseline_html):
        logging.error(f"Baseline HTML file not found: {baseline_html}")
        sys.exit(1)
    
    try:
        with open(baseline_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        html_size = os.path.getsize(baseline_html)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Count question cards
        question_cards = soup.find_all(class_='question-card')
        logging.info(f"Baseline HTML loaded ({html_size} bytes), found {len(question_cards)} question cards")
    except Exception as e:
        logging.error(f"Error loading baseline HTML: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)
    
    # Load perturbed exam data
    exam_data = load_perturbed_exam(perturbed_json)
    
    # Process each question
    questions_processed = 0
    questions_with_attacks = 0
    questions_skipped = 0
    canvas_elements_count = 0
    
    for question_card in question_cards:
        question_id = question_card.get('data-qid', '')
        if not question_id:
            logging.warning(f"Question card missing data-qid attribute, skipping")
            questions_skipped += 1
            continue
        
        logging.info(f"Processing question: {question_id}")
        questions_processed += 1
        
        # Find perturbations for this question
        perturbations = find_question_perturbations(exam_data, question_id)
        if not perturbations:
            logging.warning(f"Question {question_id}: No validated perturbations found in perturbed data, skipping")
            questions_skipped += 1
            continue
        
        # Use the validated perturbation (only one is stored per question)
        mapping = perturbations[0]
        mapping_idx = 0
        
        logging.info(f"Question {question_id}: Using pre-validated perturbation")
        logging.info(f"Question {question_id}: Original substring: '{mapping.get('original_substring', '')[:50]}...'")
        logging.info(f"Question {question_id}: Replacement substring: '{mapping.get('replacement_substring', '')[:50]}...'")
        
        # Find question prompt element
        prompt_div = question_card.find(class_='question-prompt')
        if not prompt_div:
            logging.warning(f"Question {question_id}: Could not find question-prompt element")
            questions_skipped += 1
            continue
        
        # Get original text using get_text() (same method as perturbation generation)
        # This ensures consistent text extraction between generation and attack application
        original_text = prompt_div.get_text()
        logging.debug(f"Question {question_id}: Found prompt element, original text length: {len(original_text)}")
        
        # Apply perturbation to DOM (normalization happens inside this function)
        # Normalization matches perturbation generation: ' '.join(text.split())
        perturbed_text, success = apply_perturbation_to_dom(original_text, mapping, question_id)
        if not success:
            logging.warning(f"Question {question_id}: Failed to apply perturbation, skipping")
            questions_skipped += 1
            continue
        
        # Replace text content with perturbed version
        prompt_div.clear()
        prompt_div.string = perturbed_text
        
        # Mark element for canvas rendering
        prompt_div['class'] = prompt_div.get('class', []) + ['question-to-render']
        
        # Store original text in data attribute (escape for HTML)
        import html
        escaped_original = html.escape(original_text)
        prompt_div['data-original-text'] = escaped_original
        
        logging.info(f"Question {question_id}: Element marked for canvas rendering, data attributes set")
        logging.debug(f"Question {question_id}: Original text stored (first 200 chars): {original_text[:200]}...")
        
        questions_with_attacks += 1
        canvas_elements_count += 1
    
    # Inject canvas rendering script
    script_length = inject_canvas_rendering_script(soup)
    
    # Create output directory
    output_subdir = os.path.join(output_dir, subject_name, 'image_canvas')
    os.makedirs(output_subdir, exist_ok=True)
    logging.info(f"Created output directory: {output_subdir}")
    
    # Copy CSS file
    baseline_dir = os.path.dirname(baseline_html)
    baseline_css = os.path.join(baseline_dir, 'styles.css')
    output_css = os.path.join(output_subdir, 'styles.css')
    
    if os.path.exists(baseline_css):
        try:
            shutil.copy2(baseline_css, output_css)
            logging.info(f"Copied CSS file to: {output_css}")
        except Exception as e:
            logging.error(f"Error copying CSS file: {e}")
    else:
        logging.warning(f"Baseline CSS not found at: {baseline_css}")
    
    # Create enhanced CSS file with attack-specific rules
    if questions_with_attacks > 0:
        enhanced_css_file = os.path.join(output_subdir, 'styles_enhanced.css')
        logging.info(f"Writing enhanced CSS rules to: {enhanced_css_file}")
        
        try:
            with open(enhanced_css_file, 'w', encoding='utf-8') as f:
                f.write("/* Canvas attack: Hide perturbed DOM text */\n")
                f.write(".question-to-render {\n")
                f.write("    color: transparent !important;\n")
                f.write("    -webkit-text-fill-color: transparent !important;\n")
                f.write("    text-shadow: none !important;\n")
                f.write("}\n")
            
            css_size = os.path.getsize(enhanced_css_file)
            logging.info(f"Enhanced CSS file written successfully ({css_size} bytes)")
            
            # Add link tag to HTML head
            head = soup.find('head')
            if not head:
                logging.error("No <head> tag found in HTML")
                sys.exit(1)
            
            # Check if link already exists
            existing_link = head.find('link', href='styles_enhanced.css')
            if not existing_link:
                link_tag = soup.new_tag('link', rel='stylesheet', href='styles_enhanced.css')
                head.append(link_tag)
                logging.info("Added enhanced stylesheet link to <head>")
        except Exception as e:
            logging.error(f"Error writing enhanced CSS file: {e}")
            import traceback
            logging.error(traceback.format_exc())
            sys.exit(1)
    
    # Save attacked HTML (AFTER all modifications to soup)
    output_html = os.path.join(output_subdir, 'exam.html')
    logging.info(f"Writing attacked HTML to: {output_html}")
    
    try:
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        output_size = os.path.getsize(output_html)
        logging.info(f"Attacked HTML written successfully ({output_size} bytes)")
    except Exception as e:
        logging.error(f"Error writing attacked HTML: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)
    
    # Summary
    logging.info("=" * 80)
    logging.info("Image/Canvas Attack Application Complete")
    logging.info(f"Total questions processed: {questions_processed}")
    logging.info(f"Questions with attacks applied: {questions_with_attacks}")
    logging.info(f"Questions skipped: {questions_skipped}")
    logging.info(f"Canvas elements to be created: {canvas_elements_count}")
    logging.info(f"Script injection: Success ({script_length} bytes)")
    logging.info(f"Output HTML: {output_html} ({output_size} bytes)")
    logging.info("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python 03c_apply_image_canvas_attack.py <baseline_html> <perturbed_json> <output_dir> <subject_name>")
        sys.exit(1)
    
    baseline_html = sys.argv[1]
    perturbed_json = sys.argv[2]
    output_dir = sys.argv[3]
    subject_name = sys.argv[4]
    
    apply_image_canvas_attack(baseline_html, perturbed_json, output_dir, subject_name)

