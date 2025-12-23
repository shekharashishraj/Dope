#!/usr/bin/env python3
"""
Normalize PDF-JSON exam data to unified schema.
Converts input JSON format to normalized exam_content.json format.
"""

import json
import sys
import os
import logging
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict


def setup_logging(log_dir="logs"):
    """Setup logging to file with timestamp."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"01_normalize_{timestamp}.log")
    
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


def infer_question_type(question):
    """Infer question type if not explicitly set."""
    question_type = question.get('question_type', '').upper()
    
    if question_type:
        return question_type
    
    # Check for options
    options = question.get('options')
    if options and isinstance(options, dict) and len(options) > 0:
        # Check if True/False
        option_keys = list(options.keys())
        if len(option_keys) == 2 and 'True' in option_keys and 'False' in option_keys:
            return 'TF'
        return 'MCQ'
    
    # Check stem text for True/False indicators
    stem_text = question.get('stem_text', '').lower()
    if 'true' in stem_text and 'false' in stem_text:
        return 'TF'
    
    # Default to long-form
    return 'LONG'


def normalize_options(options_dict):
    """Convert options dict to array format."""
    if not options_dict or not isinstance(options_dict, dict):
        return []
    
    options_list = []
    for key, value in options_dict.items():
        options_list.append({
            "id": key,
            "text": value
        })
    return options_list


def normalize_math_fragments(text: str) -> str:
    """Normalize simple LaTeX-style fragments into cleaner TeX/plain math.

    Handles patterns like t\^{}2, 2\^{}t, etc.
    Does NOT add TeX delimiters; just cleans the noisy \^{} notation.
    """
    if not text:
        return text

    # Step 1: clean noisy \^{} notation -> plain caret
    # t\^{}2 -> t^2, 2\^{}t -> 2^t
    cleaned = re.sub(r"\\\^{}\s*", "^", text)

    # (Optional future steps): add more regex rules here if needed
    return cleaned


def normalize_question(question, question_num):
    """Normalize a single question to the schema."""
    qid = question.get('question_id')
    if not qid:
        qid = f"Q{question_num}"
        logging.warning(f"Question {question_num} missing question_id, generated: {qid}")
    
    prompt = question.get('stem_text', '')
    if not prompt:
        logging.warning(f"Question {qid} missing stem_text")
        prompt = ""
    else:
        original_prompt = prompt
        prompt = normalize_math_fragments(prompt)
        if original_prompt != prompt:
            logging.info(f"Normalized math fragments in prompt for question {qid}")
    
    question_type = infer_question_type(question)
    if not question.get('question_type'):
        logging.info(f"Inferred question type '{question_type}' for question {qid}")
    
    normalized = {
        "id": qid,
        "prompt": prompt
    }
    
    # Add options for MCQ
    if question_type == 'MCQ':
        options = normalize_options(question.get('options'))
        if options:
            normalized["options"] = options
        else:
            logging.warning(f"MCQ question {qid} has no options")
    
    # Add metadata
    meta = {}
    if 'marks' in question:
        meta['marks'] = question['marks']
    if 'source' in question:
        meta['source'] = question['source']
    if 'gold_answer' in question:
        meta['gold_answer'] = question['gold_answer']
    if 'page' in question:
        meta['page'] = question['page']
    if 'bbox' in question:
        meta['bbox'] = question['bbox']
    
    if meta:
        normalized["meta"] = meta
    
    return normalized, question_type


def normalize_exam(input_file, output_file):
    """Main normalization function."""
    log_file = setup_logging()
    logging.info("=" * 80)
    logging.info("Starting JSON normalization")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 80)
    
    # Read input file
    logging.info(f"Reading input file: {input_file}")
    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        logging.info("Successfully loaded input JSON")
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Extract title
    title = input_data.get('document_name', 'Question Paper')
    logging.info(f"Document title: {title}")
    
    # Extract instructions (if available)
    instructions = []
    if 'instructions' in input_data:
        instructions = input_data['instructions']
        logging.info(f"Found {len(instructions)} instruction(s)")
    else:
        logging.info("No instructions found in input, using defaults")
        instructions = ["Answer all questions."]
    
    # Process questions
    questions = input_data.get('questions', [])
    logging.info(f"Processing {len(questions)} question(s)")
    
    if not questions:
        logging.warning("No questions found in input file")
    
    # Group questions by type
    sections_dict = defaultdict(list)
    type_counts = defaultdict(int)
    
    for idx, question in enumerate(questions, 1):
        normalized_q, q_type = normalize_question(question, idx)
        sections_dict[q_type].append(normalized_q)
        type_counts[q_type] += 1
        logging.debug(f"Processed question {idx}: {normalized_q['id']} (type: {q_type})")
    
    # Log type distribution
    logging.info("Question type distribution:")
    for q_type, count in type_counts.items():
        logging.info(f"  {q_type}: {count}")
    
    # Create sections
    sections = []
    section_titles = {
        'MCQ': 'Multiple Choice',
        'TF': 'True / False',
        'LONG': 'Long Form'
    }
    
    for q_type in ['MCQ', 'TF', 'LONG']:
        if q_type in sections_dict:
            section_id = f"sec_{q_type.lower()}"
            sections.append({
                "id": section_id,
                "type": q_type.lower(),
                "title": section_titles.get(q_type, q_type),
                "questions": sections_dict[q_type]
            })
            logging.info(f"Created section: {section_id} ({section_titles.get(q_type, q_type)}) with {len(sections_dict[q_type])} question(s)")
    
    # Create normalized output
    output_data = {
        "title": title,
        "instructions": instructions,
        "sections": sections
    }
    
    # Write output file
    logging.info(f"Writing normalized JSON to: {output_file}")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        logging.info("Successfully wrote normalized JSON")
        
        # Log file size
        file_size = os.path.getsize(output_file)
        logging.info(f"Output file size: {file_size} bytes")
    except Exception as e:
        logging.error(f"Error writing output file: {e}")
        sys.exit(1)
    
    # Summary
    logging.info("=" * 80)
    logging.info("Normalization complete")
    logging.info(f"Total questions: {len(questions)}")
    logging.info(f"Total sections: {len(sections)}")
    logging.info(f"Output file: {output_file}")
    logging.info("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 01_normalize_json.py <input_json> <output_json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    normalize_exam(input_file, output_file)

