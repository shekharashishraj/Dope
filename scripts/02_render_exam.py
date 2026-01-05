#!/usr/bin/env python3
"""
Render canvas-style exam HTML/CSS from normalized JSON.
Uses Jinja2 template to generate baseline exam HTML.
"""

import json
import sys
import os
import logging
import shutil
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


def setup_logging(log_dir="logs"):
    """Setup logging to file with timestamp."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"02_render_{timestamp}.log")
    
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


def extract_subject_from_path(input_file):
    """Extract domain name from input file path.
    
    Expected path pattern: Input/<domain>/<education_level>/JSON_output/<file>.json
    Returns the domain name (e.g., 'chemistry', 'mathematics').
    """
    input_path = Path(input_file)
    parts = input_path.parts
    
    try:
        input_idx = [p.lower() for p in parts].index('input')
        if input_idx + 1 < len(parts):
            return parts[input_idx + 1]
    except ValueError:
        pass
    
    # Fallback from the tail
    try:
        if len(parts) >= 4:
            return parts[-4]
    except Exception:
        pass
    
    logging.warning(f"Could not extract domain from path {input_file}, using 'default'")
    return 'default'


def extract_education_level_from_path(input_file):
    """Extract education level from input file path.
    
    Expected path pattern: Input/<domain>/<education_level>/JSON_output/<file>.json
    """
    input_path = Path(input_file)
    parts = input_path.parts
    
    try:
        input_idx = [p.lower() for p in parts].index('input')
        if input_idx + 2 < len(parts):
            return parts[input_idx + 2]
    except ValueError:
        pass
    
    try:
        if len(parts) >= 3:
            return parts[-3]
    except Exception:
        pass
    
    logging.warning(f"Could not extract education level from path {input_file}, using 'default'")
    return 'default'


def normalize_prompt_text(text: str) -> str:
    """Normalize prompt text by stripping leading/trailing whitespace and normalizing internal whitespace.
    
    Args:
        text: The prompt text to normalize
        
    Returns:
        Normalized text with collapsed whitespace
    """
    if not text:
        return ""
    # Strip leading/trailing whitespace and normalize internal whitespace
    # This collapses multiple spaces/newlines/tabs to single spaces
    return ' '.join(text.split())


def render_exam(input_file, output_dir, subject_name=None, attack_variant="baseline"):
    """Main rendering function."""
    log_file = setup_logging()
    logging.info("=" * 80)
    logging.info("Starting exam HTML rendering")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 80)
    
    # Read input JSON
    logging.info(f"Reading normalized JSON: {input_file}")
    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            exam_data = json.load(f)
        logging.info("Successfully loaded exam data")
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Validate exam data structure
    required_keys = ['title', 'sections']
    for key in required_keys:
        if key not in exam_data:
            logging.error(f"Missing required key in exam data: {key}")
            sys.exit(1)
    
    logging.info(f"Exam title: {exam_data['title']}")
    logging.info(f"Number of sections: {len(exam_data['sections'])}")
    
    # Normalize prompt text for all questions to ensure clean whitespace
    logging.info("Normalizing prompt text for all questions...")
    normalized_count = 0
    for section in exam_data['sections']:
        for question in section.get('questions', []):
            if 'prompt' in question and question['prompt']:
                original_prompt = question['prompt']
                normalized_prompt = normalize_prompt_text(original_prompt)
                if original_prompt != normalized_prompt:
                    question['prompt'] = normalized_prompt
                    normalized_count += 1
    if normalized_count > 0:
        logging.info(f"Normalized prompt text for {normalized_count} question(s)")
    
    # Count questions
    total_questions = sum(len(section.get('questions', [])) for section in exam_data['sections'])
    logging.info(f"Total questions: {total_questions}")
    
    # Detect TeX usage for logging (MathJax will render TeX client-side)
    logging.info("Scanning exam content for TeX delimiters (for MathJax rendering)...")
    for section in exam_data['sections']:
        tex_expressions = 0
        for question in section.get('questions', []):
            prompt = question.get('prompt', '') or ''
            tex_expressions += prompt.count('\\(') + prompt.count('$$') + prompt.count('$')
            for option in question.get('options', []):
                text = option.get('text', '') or ''
                tex_expressions += text.count('\\(') + text.count('$$') + text.count('$')
        logging.info(f"Section {section.get('id', 'unknown')}: approximately {tex_expressions // 2} TeX expression(s) detected")
    
    logging.info("Skipping server-side LaTeX->MathML conversion; TeX will be rendered client-side by MathJax.")
    
    # Setup Jinja2 environment
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    logging.info(f"Template directory: {template_dir}")
    
    if not os.path.exists(template_dir):
        logging.error(f"Template directory not found: {template_dir}")
        sys.exit(1)
    
    try:
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('exam_base.html.j2')
        logging.info("Successfully loaded Jinja2 template")
    except TemplateNotFound:
        logging.error(f"Template not found: exam_base.html.j2")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading template: {e}")
        sys.exit(1)
    
    # Extract subject name from input path if not provided
    if subject_name is None:
        domain = extract_subject_from_path(input_file)
        edu_level = extract_education_level_from_path(input_file)
        subject_name = f"{domain}/{edu_level}" if edu_level else domain
        logging.info(f"Extracted domain: {domain}")
        logging.info(f"Extracted education level: {edu_level}")
        logging.info(f"Subject name: {subject_name}")
    else:
        logging.info(f"Using provided subject name: {subject_name}")
    
    # Derive exam_id from title (sanitize for use as ID)
    exam_title = exam_data.get('title', 'Unknown Exam')
    exam_id = exam_title.lower().replace(' ', '_').replace('-', '_')
    # Remove special characters, keep only alphanumeric and underscores
    exam_id = ''.join(c if c.isalnum() or c == '_' else '' for c in exam_id)
    logging.info(f"Derived exam_id: {exam_id}")
    
    # Set education level (default to K-12, can be extracted from title if needed)
    education_level = "K-12"
    if "k-12" in exam_title.lower() or "k12" in exam_title.lower():
        education_level = "K-12"
    elif "college" in exam_title.lower() or "university" in exam_title.lower():
        education_level = "College"
    elif "graduate" in exam_title.lower():
        education_level = "Graduate"
    logging.info(f"Education level: {education_level}")
    logging.info(f"Attack variant: {attack_variant}")
    
    # Render HTML
    logging.info("Rendering HTML from template...")
    try:
        html_content = template.render(
            title=exam_data['title'],
            instructions=exam_data.get('instructions', []),
            sections=exam_data['sections'],
            subject_name=subject_name,
            exam_id=exam_id,
            education_level=education_level,
            attack_variant=attack_variant
        )
        logging.info("Successfully rendered HTML with metadata")
    except Exception as e:
        logging.error(f"Error rendering template: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)
    
    # Create subject-specific output directory
    subject_output_dir = os.path.join(output_dir, subject_name)
    os.makedirs(subject_output_dir, exist_ok=True)
    logging.info(f"Output directory: {subject_output_dir}")
    
    # Write HTML file
    html_file = os.path.join(subject_output_dir, 'exam.html')
    logging.info(f"Writing HTML to: {html_file}")
    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        html_size = os.path.getsize(html_file)
        logging.info(f"HTML file written successfully ({html_size} bytes)")
    except Exception as e:
        logging.error(f"Error writing HTML file: {e}")
        sys.exit(1)
    
    # Copy CSS file
    css_source = os.path.join(template_dir, 'styles.css')
    css_dest = os.path.join(subject_output_dir, 'styles.css')
    
    logging.info(f"Copying CSS from: {css_source}")
    if not os.path.exists(css_source):
        logging.error(f"CSS file not found: {css_source}")
        sys.exit(1)
    
    try:
        shutil.copy2(css_source, css_dest)
        css_size = os.path.getsize(css_dest)
        logging.info(f"CSS file copied successfully ({css_size} bytes)")
    except Exception as e:
        logging.error(f"Error copying CSS file: {e}")
        sys.exit(1)
    
    # Validate HTML structure
    logging.info("Validating HTML structure...")
    if '<html' in html_content and '<body' in html_content:
        logging.info("HTML structure validation passed")
    else:
        logging.warning("HTML structure validation: missing expected tags")
    
    # Count sections and questions in rendered HTML
    section_count = html_content.count('class="section"')
    question_count = html_content.count('class="question-card"')
    logging.info(f"Rendered HTML contains {section_count} section(s) and {question_count} question card(s)")
    
    # Summary
    logging.info("=" * 80)
    logging.info("Rendering complete")
    logging.info(f"Subject: {subject_name}")
    logging.info(f"HTML file: {html_file} ({html_size} bytes)")
    logging.info(f"CSS file: {css_dest} ({css_size} bytes)")
    logging.info(f"Total questions rendered: {total_questions}")
    logging.info("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python 02_render_exam.py <input_json> <output_dir> [subject_name] [attack_variant]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    subject_name = sys.argv[3] if len(sys.argv) > 3 else None
    attack_variant = sys.argv[4] if len(sys.argv) > 4 else "baseline"
    
    render_exam(input_file, output_dir, subject_name, attack_variant)

