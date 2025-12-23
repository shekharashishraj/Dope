#!/usr/bin/env python3
"""
Apply CSS ::before attack to baseline HTML using perturbations.
Replaces substrings in DOM with perturbed versions while showing original via CSS ::before.
"""

import json
import sys
import os
import logging
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple


def setup_logging(log_dir="logs"):
    """Setup logging to file with timestamp."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"03b_css_before_{timestamp}.log")
    
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


def apply_substring_replacement(text: str, mapping: Dict, question_id: str):
    """Replace substring at exact position in text."""
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
    logging.debug(f"Question {question_id}: Text before replacement (first 200 chars): {text[:200]}...")
    logging.debug(f"Question {question_id}: Text after replacement (first 200 chars): {new_text[:200]}...")
    
    return new_text, True


def inject_css_before_rules(soup: BeautifulSoup, question_id: str, mapping: Dict, mapping_idx: int) -> Tuple[str, str]:
    """Generate obfuscated CSS class name and return CSS rule.
    
    Returns:
        Tuple of (main_class, css_rule)
    """
    # Generate deterministic hash-based class name
    seed = f"{question_id}{mapping_idx}"
    hash_digest = hashlib.sha256(seed.encode()).hexdigest()[:12]
    
    # Generate obfuscated class name: c=container
    main_class = f"c{hash_digest}"
    
    original_substring = mapping.get('original_substring', '')
    # Escape quotes in content for CSS
    escaped_content = original_substring.replace('"', '\\"').replace("'", "\\'")
    
    css_rule = f"""
.{main_class} {{
    position: relative;
    display: inline;
    font: inherit;
    line-height: inherit;
    vertical-align: baseline;
    color: inherit;
}}
.{main_class} > .orig {{
    user-select: none;
    pointer-events: none;
}}
.{main_class} > .r {{
    color: transparent;
    position: absolute;
    left: 0;
    top: 0;
    white-space: nowrap;
}}"""
    
    logging.info(f"Question {question_id}: Generated CSS rule for mapping {mapping_idx}, class: {main_class}")
    logging.debug(f"Question {question_id}: CSS rule: {css_rule}")
    
    return main_class, css_rule


def write_width_calculation_script(output_dir: str, text_lookup: Dict[str, str]) -> str:
    """Write JavaScript for width calculation to external file.
    
    Args:
        output_dir: Directory to write the JS file
        text_lookup: Dictionary mapping class names to original text
    
    Returns:
        Path to the written JS file
    """
    # Generate JavaScript lookup object
    lookup_lines = ["var w={};"]
    for class_name, original_text in text_lookup.items():
        # Escape special characters for JavaScript string (single-quoted)
        escaped_text = (original_text
                       .replace('\\', '\\\\')  # Backslash first
                       .replace("'", "\\'")    # Single quote
                       .replace('"', '\\"')    # Double quote
                       .replace('\n', '\\n')   # Newline
                       .replace('\r', '\\r')   # Carriage return
                       .replace('\t', '\\t'))  # Tab
        lookup_lines.append(f"w['{class_name}']='{escaped_text}';")
    
    lookup_js = '\n'.join(lookup_lines)
    
    # Generate width calculation code
    width_calc_js = """
document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('[class^="c"]').forEach(function(el){
    var cls=el.className;
    if(w[cls]){
      var temp=document.createElement('span');
      temp.style.visibility='hidden';
      temp.style.position='absolute';
      temp.style.whiteSpace='nowrap';
      var computed=getComputedStyle(el.parentElement);
      temp.style.fontSize=computed.fontSize;
      temp.style.fontFamily=computed.fontFamily;
      temp.style.lineHeight=computed.lineHeight;
      temp.textContent=w[cls];
      document.body.appendChild(temp);
      el.style.width=temp.offsetWidth+'px';
      document.body.removeChild(temp);
    }
  });
});"""
    
    # Combine into single script
    script_content = lookup_js + width_calc_js
    
    # Write to external file
    js_file = os.path.join(output_dir, 'width_calc.js')
    logging.info(f"Writing JavaScript to external file: {js_file}")
    
    try:
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        script_size = os.path.getsize(js_file)
        logging.info(f"JavaScript file written successfully ({script_size} bytes, {len(text_lookup)} mappings)")
        logging.debug(f"JavaScript code (first 500 chars): {script_content[:500]}...")
        
        return js_file
    except Exception as e:
        logging.error(f"Error writing JavaScript file: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)


def apply_css_before_attack(baseline_html: str, perturbed_json: str, output_dir: str, subject_name: str):
    """Main function to apply CSS ::before attack."""
    log_file = setup_logging()
    logging.info("=" * 80)
    logging.info("Starting CSS ::before Attack Application")
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
    total_css_rules = 0
    css_rules_list = []
    text_lookup = {}  # Dictionary mapping class names to original text for JavaScript
    
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
        
        # Get text content using get_text() (same method as perturbation generation)
        # This ensures consistent text extraction between generation and attack application
        prompt_text = prompt_div.get_text()
        logging.debug(f"Question {question_id}: Found prompt element, text length: {len(prompt_text)}")
        
        # Apply substring replacement (normalization happens inside this function)
        # Normalization matches perturbation generation: ' '.join(text.split())
        new_text, success = apply_substring_replacement(prompt_text, mapping, question_id)
        if not success:
            logging.warning(f"Question {question_id}: Failed to apply substring replacement, skipping")
            questions_skipped += 1
            continue
        
        # Generate obfuscated CSS class name and rule
        main_class, css_rule = inject_css_before_rules(soup, question_id, mapping, mapping_idx)
        css_rules_list.append(css_rule)
        total_css_rules += 1
        
        # Store original text in lookup for JavaScript width calculation
        original_substring = mapping.get('original_substring', '')
        text_lookup[main_class] = original_substring
        
        # Replace text content and wrap in single span
        prompt_div.clear()
        
        # Split text around the replacement position
        start_pos = mapping.get('start_pos', 0)
        replacement_substring = mapping.get('replacement_substring', '')
        
        # Create text before replacement
        before_text = new_text[:start_pos]
        # Create text after replacement
        after_text = new_text[start_pos + len(replacement_substring):]
        
        # Build new content with single span
        if before_text:
            prompt_div.append(before_text)
        
        # Create span with both original and replacement text spans
        span = soup.new_tag('span')
        span['class'] = main_class
        
        # Original text span (visible, not selectable)
        orig_span = soup.new_tag('span')
        orig_span['class'] = 'orig'
        orig_span.string = original_substring
        
        # Replacement text span (hidden, selectable)
        repl_span = soup.new_tag('span')
        repl_span['class'] = 'r'
        repl_span.string = replacement_substring
        
        span.append(orig_span)
        span.append(repl_span)
        prompt_div.append(span)
        
        if after_text:
            prompt_div.append(after_text)
        
        logging.info(f"Question {question_id}: CSS rule generated, class: {main_class}")
        questions_with_attacks += 1
    
    # Create output directory
    output_subdir = os.path.join(output_dir, subject_name, 'css_before')
    os.makedirs(output_subdir, exist_ok=True)
    logging.info(f"Created output directory: {output_subdir}")
    
    # Write CSS rules to external file
    if css_rules_list:
        css_file = os.path.join(output_subdir, 'styles_enhanced.css')
        logging.info(f"Writing CSS rules to external file: {css_file}")
        
        try:
            with open(css_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(css_rules_list))
            
            css_size = os.path.getsize(css_file)
            logging.info(f"CSS file written successfully ({css_size} bytes, {total_css_rules} rules)")
        except Exception as e:
            logging.error(f"Error writing CSS file: {e}")
            import traceback
            logging.error(traceback.format_exc())
            sys.exit(1)
        
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
            logging.info("Added stylesheet link to <head>")
    
    # Write JavaScript to external file
    if text_lookup:
        js_file = write_width_calculation_script(output_subdir, text_lookup)
        
        # Add script tag to HTML head
        head = soup.find('head')
        if not head:
            logging.error("No <head> tag found in HTML")
            sys.exit(1)
        
        # Check if script already exists
        existing_script = head.find('script', src='width_calc.js')
        if not existing_script:
            script_tag = soup.new_tag('script', src='width_calc.js')
            head.append(script_tag)
            logging.info("Added JavaScript script tag to <head>")
    
    # Save attacked HTML
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
    
    # Summary
    logging.info("=" * 80)
    logging.info("CSS ::before Attack Application Complete")
    logging.info(f"Total questions processed: {questions_processed}")
    logging.info(f"Questions with attacks applied: {questions_with_attacks}")
    logging.info(f"Questions skipped: {questions_skipped}")
    logging.info(f"Total CSS rules injected: {total_css_rules}")
    logging.info(f"Output HTML: {output_html} ({output_size} bytes)")
    logging.info("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python 03b_apply_css_before_attack.py <baseline_html> <perturbed_json> <output_dir> <subject_name>")
        sys.exit(1)
    
    baseline_html = sys.argv[1]
    perturbed_json = sys.argv[2]
    output_dir = sys.argv[3]
    subject_name = sys.argv[4]
    
    apply_css_before_attack(baseline_html, perturbed_json, output_dir, subject_name)

