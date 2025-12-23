#!/usr/bin/env python3
"""
Generate perturbations for exam questions using LLM API.
Adapts normalized exam JSON format to perturbation generator format and calls OpenAI API.
"""

import json
import sys
import os
import logging
import re
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to Python path to allow importing prompts module
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

try:
    from openai import OpenAI
except ImportError:
    logging.error("openai package not installed. Install with: pip install openai")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # python-dotenv not installed, skip .env loading

try:
    from bs4 import BeautifulSoup
except ImportError:
    logging.error("beautifulsoup4 package not installed. Install with: pip install beautifulsoup4")
    sys.exit(1)

from prompts.mcq_prompt import format_mcq_prompt
from prompts.tf_prompt import format_tf_prompt
from prompts.long_prompt import format_long_prompt


def setup_logging(log_dir="logs"):
    """Setup logging to file with timestamp."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"01b_generate_perturbations_{timestamp}.log")
    
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


def load_normalized_exam(input_file):
    """Load normalized exam JSON file."""
    logging.info(f"Loading normalized exam JSON: {input_file}")
    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            exam_data = json.load(f)
        
        file_size = os.path.getsize(input_file)
        num_sections = len(exam_data.get('sections', []))
        total_questions = sum(len(s.get('questions', [])) for s in exam_data.get('sections', []))
        
        logging.info(f"Successfully loaded exam data ({file_size} bytes)")
        logging.info(f"Number of sections: {num_sections}")
        logging.info(f"Total questions: {total_questions}")
        
        return exam_data
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading input file: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)


def load_html_and_extract_texts(html_file: str) -> Dict[str, str]:
    """Load HTML file and extract question prompt texts.
    
    Returns a dictionary mapping question_id -> prompt_text.
    Uses the same method as attack scripts: find question card by data-qid,
    then get text from .question-prompt element using get_text().
    """
    if not html_file or not os.path.exists(html_file):
        logging.warning(f"HTML file not found: {html_file}")
        return {}
    
    logging.info(f"Loading HTML file: {html_file}")
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        question_texts = {}
        
        # Find all question cards
        question_cards = soup.find_all(class_='question-card')
        logging.info(f"Found {len(question_cards)} question cards in HTML")
        
        for card in question_cards:
            question_id = card.get('data-qid')
            if not question_id:
                logging.warning("Question card missing data-qid attribute, skipping")
                continue
            
            # Find prompt element (same as attack scripts)
            prompt_div = card.find(class_='question-prompt')
            if not prompt_div:
                logging.warning(f"Question {question_id}: Could not find question-prompt element")
                continue
            
            # Extract text using get_text() (same method as attack scripts)
            prompt_text = prompt_div.get_text()
            # Normalize whitespace: strip leading/trailing, normalize internal whitespace to single spaces
            # This ensures consistent position calculation
            prompt_text = ' '.join(prompt_text.split())
            question_texts[question_id] = prompt_text
            logging.debug(f"Question {question_id}: Extracted text, length={len(prompt_text)}")
        
        logging.info(f"Successfully extracted text for {len(question_texts)} questions from HTML")
        return question_texts
        
    except Exception as e:
        logging.error(f"Error loading HTML file: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {}


def extract_question_number(question_id: str, question_index: int) -> int:
    """Extract question number from question ID or use index."""
    # Try to extract number from ID (e.g., "mathematics_k-12_doc_01_mathematics_mcq_1" -> 1)
    match = re.search(r'_(\d+)$', question_id)
    if match:
        return int(match.group(1))
    # Fallback to index
    return question_index


def map_options_array_to_dict(options_array: List[Dict]) -> Dict[str, str]:
    """Convert options array to dictionary format."""
    options_dict = {}
    for opt in options_array:
        opt_id = opt.get('id', '')
        opt_text = opt.get('text', '')
        if opt_id:
            options_dict[opt_id] = opt_text
    return options_dict


def extract_gold_answer(question: Dict, section_type: str) -> Optional[str]:
    """Extract gold answer from question metadata or infer from options."""
    # Try to get from meta
    meta = question.get('meta', {})
    if 'gold_answer' in meta:
        return meta['gold_answer']
    
    # For MCQ, we might need to infer (but this is not reliable without answer key)
    # For TF, we can't infer
    # For LONG, we can't infer
    
    logging.warning(f"Could not find gold_answer for question {question.get('id', 'unknown')}")
    return None


def map_to_perturbation_format(question: Dict, section_type: str, question_index: int, html_text: Optional[str] = None) -> Optional[Dict]:
    """Convert normalized question format to perturbation generator format.
    
    Args:
        question: Question dict from normalized JSON
        section_type: Section type (mcq, tf, long)
        question_index: Question index
        html_text: Optional HTML-extracted text (if None, uses JSON prompt)
    """
    question_id = question.get('id', '')
    if not question_id:
        logging.warning(f"Question missing ID at index {question_index}")
        return None
    
    # Extract question number
    question_number = extract_question_number(question_id, question_index)
    
    # Get prompt text - prefer HTML text if available, otherwise use JSON prompt
    if html_text:
        prompt = html_text
        logging.debug(f"Question {question_id}: Using HTML-extracted text (length={len(prompt)})")
    else:
        prompt = question.get('prompt', '')
        if not prompt:
            logging.warning(f"Question {question_id} missing prompt")
            return None
        logging.debug(f"Question {question_id}: Using JSON prompt text (length={len(prompt)})")
    
    # Map section type to question type
    type_mapping = {
        'mcq': 'MCQ',
        'tf': 'TF',
        'long': 'LONG'
    }
    question_type = type_mapping.get(section_type.lower(), section_type.upper())
    
    # Map options (array to dict for MCQ)
    options = {}
    if question_type == 'MCQ':
        options_array = question.get('options', [])
        options = map_options_array_to_dict(options_array)
    
    # Extract gold answer
    gold_answer = extract_gold_answer(question, section_type)
    
    # Validate gold_answer is present (required for perturbation generation)
    if not gold_answer:
        logging.error(f"Question {question_id}: Missing gold_answer - required for perturbation generation. Skipping.")
        return None
    
    # Log mapping details
    logging.info(f"Question {question_id}: type={question_type}, prompt_length={len(prompt)}, "
                 f"num_options={len(options)}, gold_answer={gold_answer}")
    
    return {
        'question_id': question_id,
        'question_number': question_number,
        'question_type': question_type,
        'latex_stem_text': prompt,
        'copyable_text': prompt,
        'options': options,
        'gold_answer': gold_answer or '',
        'original_question': question
    }


def format_prompt_for_question(question_data: Dict, k: int = 3) -> Optional[str]:
    """Format prompt for question using appropriate template."""
    question_id = question_data['question_id']
    question_type = question_data['question_type']
    question_number = question_data['question_number']
    
    try:
        if question_type == 'MCQ':
            prompt = format_mcq_prompt(
                latex_stem_text=question_data['latex_stem_text'],
                copyable_text=question_data['copyable_text'],
                gold_answer=question_data['gold_answer'],
                question_type=question_type,
                options=question_data['options'],
                question_index=question_number,
                k=k,
                reasoning_steps="",
                prefix_note="",
                answer_guidance="",
                retry_instructions=""
            )
        elif question_type == 'TF':
            prompt = format_tf_prompt(
                latex_stem_text=question_data['latex_stem_text'],
                copyable_text=question_data['copyable_text'],
                gold_answer=question_data['gold_answer'],
                question_type=question_type,
                question_index=question_number,
                k=k,
                reasoning_steps="",
                prefix_note="",
                answer_guidance="",
                retry_instructions=""
            )
        elif question_type == 'LONG':
            prompt = format_long_prompt(
                latex_stem_text=question_data['latex_stem_text'],
                copyable_text=question_data['copyable_text'],
                gold_answer=question_data['gold_answer'],
                question_type=question_type,
                question_index=question_number,
                k=k,
                reasoning_steps="",
                prefix_note="",
                answer_guidance="",
                retry_instructions=""
            )
        else:
            logging.warning(f"Unknown question type: {question_type} for question {question_id}")
            return None
        
        logging.info(f"Question {question_id}: Prompt formatted, length={len(prompt)} chars")
        logging.debug(f"Question {question_id} prompt preview (first 500 chars): {prompt[:500]}...")
        
        return prompt
    except Exception as e:
        logging.error(f"Error formatting prompt for question {question_id}: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None


def call_openai_api(client: OpenAI, prompt: str, model: str = "gpt-4o", question_id: str = None, max_retries: int = 3):
    """Make API call to generate perturbations."""
    api_start_time = time.time()
    logging.info(f"Question {question_id}: Starting API call, model={model}, prompt_length={len(prompt)}")
    
    # Log prompt details at DEBUG level
    if len(prompt) > 2000:
        logging.debug(f"Question {question_id}: Full prompt (truncated, first 1000 chars): {prompt[:1000]}...")
    else:
        logging.debug(f"Question {question_id}: Full prompt: {prompt}")
    
    for attempt in range(max_retries):
        try:
            logging.debug(f"Question {question_id}: API call attempt {attempt + 1}/{max_retries}")
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            api_end_time = time.time()
            api_duration = api_end_time - api_start_time
            
            # Extract response details
            response_text = response.choices[0].message.content
            tokens_used = getattr(response.usage, 'total_tokens', None) if hasattr(response, 'usage') else None
            
            logging.info(f"Question {question_id}: API call successful, duration={api_duration:.2f}s, "
                        f"response_length={len(response_text)}, tokens_used={tokens_used}")
            
            # Log response at DEBUG level
            if len(response_text) > 1000:
                logging.debug(f"Question {question_id}: API response (truncated, first 1000 chars): {response_text[:1000]}...")
            else:
                logging.debug(f"Question {question_id}: API response: {response_text}")
            
            return response_text
            
        except Exception as e:
            api_end_time = time.time()
            api_duration = api_end_time - api_start_time
            
            logging.warning(f"Question {question_id}: API call attempt {attempt + 1} failed after {api_duration:.2f}s: {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logging.info(f"Question {question_id}: Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error(f"Question {question_id}: All {max_retries} API call attempts failed")
                import traceback
                logging.error(traceback.format_exc())
                return None
    
    return None


def validate_perturbation(mapping: Dict, html_text: str, question_id: str) -> tuple[bool, Optional[str]]:
    """Validate and auto-correct perturbation mapping. Returns (is_valid, failure_reason).
    
    Returns True if:
    - original_substring exists in html_text
    - Position is within bounds (auto-corrected if needed)
    - Substring at position matches original_substring
    
    Args:
        mapping: Perturbation mapping dict with original_substring, replacement_substring, start_pos, end_pos, 
                 and optionally left_context, right_context
        html_text: HTML-extracted text to validate against (should already be normalized)
        question_id: Question ID for logging
    """
    original_substring = mapping.get('original_substring', '')
    replacement_substring = mapping.get('replacement_substring', '')
    start_pos = mapping.get('start_pos', -1)
    end_pos = mapping.get('end_pos', -1)
    left_context = mapping.get('left_context', '')
    right_context = mapping.get('right_context', '')
    
    # Normalize all text (same normalization as HTML extraction)
    original_substring = ' '.join(original_substring.split())
    replacement_substring = ' '.join(replacement_substring.split())
    html_text_normalized = ' '.join(html_text.split())
    
    # Check required fields
    if not original_substring or not replacement_substring:
        logging.warning(f"Question {question_id}: Invalid mapping (empty substring)")
        return False, 'empty_substring'
    
    # Validate position format
    if start_pos < 0 or end_pos < 0 or start_pos >= end_pos:
        logging.warning(f"Question {question_id}: Invalid positions [{start_pos}, {end_pos})")
        return False, 'position_error'
    
    # Try to validate at LLM's position first
    if start_pos + len(original_substring) <= len(html_text_normalized):
        actual_substring = html_text_normalized[start_pos:start_pos + len(original_substring)]
        if actual_substring == original_substring:
            # Position is correct!
            logging.info(f"Question {question_id}: Perturbation validated successfully at position {start_pos}")
            return True, None
    
    # Auto-correction: Find actual position
    # First, try with context if available (most reliable for disambiguation)
    if left_context and right_context:
        left_context_normalized = ' '.join(left_context.split())
        right_context_normalized = ' '.join(right_context.split())
        # Construct search pattern: left_context + original_substring + right_context
        search_pattern = left_context_normalized + ' ' + original_substring + ' ' + right_context_normalized
        pattern_pos = html_text_normalized.find(search_pattern)
        if pattern_pos >= 0:
            # Found with context, extract just the substring position
            actual_pos = pattern_pos + len(left_context_normalized) + 1  # +1 for space
            # Verify it's correct
            if actual_pos + len(original_substring) <= len(html_text_normalized):
                actual_substring = html_text_normalized[actual_pos:actual_pos + len(original_substring)]
                if actual_substring == original_substring:
                    # Auto-correct the position
                    mapping['start_pos'] = actual_pos
                    mapping['end_pos'] = actual_pos + len(original_substring)
                    logging.info(f"Question {question_id}: Auto-corrected position using context: [{actual_pos}, {mapping['end_pos']})")
                    return True, None
    
    # Fallback: Simple find (first occurrence)
    actual_pos = html_text_normalized.find(original_substring)
    if actual_pos >= 0:
        # Found it! Auto-correct the position
        mapping['start_pos'] = actual_pos
        mapping['end_pos'] = actual_pos + len(original_substring)
        logging.info(f"Question {question_id}: Auto-corrected position: [{actual_pos}, {mapping['end_pos']})")
        
        # Validate bounds
        if actual_pos + len(original_substring) > len(html_text_normalized):
            return False, 'length_violation'
        
        return True, None
    
    # Not found at all - log detailed error
    logging.warning(f"Question {question_id}: Substring mismatch at position {start_pos}. "
                 f"Expected: '{original_substring[:50]}...', "
                 f"Found: '{html_text_normalized[start_pos:start_pos+50] if start_pos < len(html_text_normalized) else 'OUT OF BOUNDS'}...'")
    # Also try to find the substring in the text to help debug
    if original_substring in html_text_normalized:
        found_pos = html_text_normalized.find(original_substring)
        logging.warning(f"Question {question_id}: Substring exists in text at position {found_pos} (not at expected {start_pos})")
    return False, 'substring_mismatch'


def select_best_perturbation(perturbations: List[Dict], html_text: str, question_id: str) -> tuple[Optional[Dict], Optional[str]]:
    """Select the best perturbation from a list by validating each one.
    
    Returns (best_perturbation, failure_reason_if_all_failed).
    
    Args:
        perturbations: List of perturbation mappings
        html_text: HTML-extracted text to validate against
        question_id: Question ID for logging
    """
    if not perturbations:
        logging.warning(f"Question {question_id}: No perturbations to validate")
        return None, 'no_perturbations'
    
    if not html_text:
        logging.warning(f"Question {question_id}: No HTML text available for validation, using first perturbation")
        return perturbations[0] if perturbations else None, None
    
    failure_reasons_list = []
    
    for idx, perturbation in enumerate(perturbations):
        is_valid, failure_reason = validate_perturbation(perturbation, html_text, question_id)
        if is_valid:
            logging.info(f"Question {question_id}: Selected perturbation {idx + 1} of {len(perturbations)} (validated)")
            return perturbation, None
        else:
            failure_reasons_list.append(failure_reason)
            logging.warning(f"Question {question_id}: Perturbation {idx + 1} of {len(perturbations)} failed validation (see details above)")
    
    # Return most common failure reason
    if failure_reasons_list:
        most_common = max(set(failure_reasons_list), key=failure_reasons_list.count)
        logging.warning(f"Question {question_id}: All {len(perturbations)} perturbations failed validation")
        return None, most_common
    
    return None, 'no_perturbations'


def parse_perturbation_response(response_text: str, question_id: str) -> Optional[List[Dict]]:
    """Parse JSON response from API into list of mappings."""
    if not response_text:
        logging.error(f"Question {question_id}: Empty response from API")
        return None
    
    try:
        # Try to parse as JSON object first (might be wrapped)
        response_data = json.loads(response_text)
        
        # Handle different response formats
        if isinstance(response_data, list):
            mappings = response_data
        elif isinstance(response_data, dict):
            # Look for common keys that might contain the array
            if 'mappings' in response_data:
                mappings = response_data['mappings']
            elif 'perturbations' in response_data:
                mappings = response_data['perturbations']
            elif 'results' in response_data:
                mappings = response_data['results']
            else:
                # Try to find any array in the response
                arrays = [v for v in response_data.values() if isinstance(v, list)]
                if arrays:
                    mappings = arrays[0]
                else:
                    logging.error(f"Question {question_id}: Could not find mappings array in response")
                    logging.debug(f"Question {question_id}: Response structure: {list(response_data.keys())}")
                    return None
        else:
            logging.error(f"Question {question_id}: Unexpected response type: {type(response_data)}")
            return None
        
        logging.info(f"Question {question_id}: Parsed {len(mappings)} mappings from response")
        
        # Validate and log each mapping
        for idx, mapping in enumerate(mappings):
            original = mapping.get('original_substring', '')
            replacement = mapping.get('replacement_substring', '')
            start_pos = mapping.get('start_pos', -1)
            end_pos = mapping.get('end_pos', -1)
            
            logging.debug(f"Question {question_id}: Mapping {idx + 1}: original='{original[:50]}...', "
                         f"replacement='{replacement[:50]}...', positions=[{start_pos}, {end_pos})")
            
            # Validate mapping structure
            required_fields = ['original_substring', 'replacement_substring', 'start_pos', 'end_pos']
            missing_fields = [f for f in required_fields if f not in mapping]
            if missing_fields:
                logging.warning(f"Question {question_id}: Mapping {idx + 1} missing fields: {missing_fields}")
        
        return mappings
        
    except json.JSONDecodeError as e:
        logging.error(f"Question {question_id}: JSON parsing error: {e}")
        logging.debug(f"Question {question_id}: Raw response (first 500 chars): {response_text[:500]}...")
        return None
    except Exception as e:
        logging.error(f"Question {question_id}: Error parsing response: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None


def merge_perturbations_into_exam(exam_data: Dict, perturbations_dict: Dict[str, List[Dict]]):
    """Store perturbations in question objects."""
    total_perturbations = 0
    questions_with_perturbations = 0
    questions_without_perturbations = 0
    
    for section in exam_data.get('sections', []):
        for question in section.get('questions', []):
            question_id = question.get('id', '')
            if question_id in perturbations_dict:
                perturbations = perturbations_dict[question_id]
                question['perturbations'] = perturbations
                total_perturbations += len(perturbations)
                questions_with_perturbations += 1
                logging.info(f"Question {question_id}: Stored {len(perturbations)} perturbations")
            else:
                question['perturbations'] = []
                questions_without_perturbations += 1
                logging.warning(f"Question {question_id}: No perturbations generated")
    
    logging.info(f"Perturbation merge summary: {questions_with_perturbations} questions with perturbations, "
                f"{questions_without_perturbations} questions without perturbations, "
                f"total perturbations: {total_perturbations}")
    
    return total_perturbations


def generate_perturbations(input_file: str, output_file: str, api_key: str, model: str = "gpt-4o", k: int = 3, baseline_html: Optional[str] = None):
    """Main function to generate perturbations for all questions."""
    log_file = setup_logging()
    logging.info("=" * 80)
    logging.info("Starting Perturbation Generation")
    logging.info(f"Input file: {input_file}")
    logging.info(f"Output file: {output_file}")
    logging.info(f"API model: {model}")
    logging.info(f"Perturbations per question (k): {k}")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 80)
    
    # Load exam data
    exam_data = load_normalized_exam(input_file)
    
    # Load HTML and extract question texts (if baseline_html provided)
    html_texts = {}
    if baseline_html:
        logging.info(f"Loading baseline HTML: {baseline_html}")
        html_texts = load_html_and_extract_texts(baseline_html)
        if html_texts:
            logging.info(f"Successfully loaded HTML texts for {len(html_texts)} questions")
        else:
            logging.warning("No HTML texts extracted, will use JSON prompt text instead")
    else:
        logging.info("No baseline HTML provided, using JSON prompt text")
    
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=api_key)
        logging.info("OpenAI client initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {e}")
        sys.exit(1)
    
    # Process all questions
    total_questions = 0
    successful_questions = 0
    failed_questions = 0
    total_api_calls = 0
    successful_api_calls = 0
    failed_api_calls = 0
    api_start_time = time.time()
    perturbations_dict = {}
    
    # Failure tracking
    failure_reasons = {
        'missing_gold_answer': [],
        'json_parse_error': [],
        'substring_mismatch': [],
        'position_error': [],
        'length_violation': [],
        'empty_substring': [],
        'api_call_failed': [],
        'no_valid_perturbations': []
    }
    
    for section in exam_data.get('sections', []):
        section_type = section.get('type', '')
        questions = section.get('questions', [])
        
        logging.info(f"Processing section: {section.get('id', 'unknown')} ({section_type}), "
                    f"{len(questions)} questions")
        
        for idx, question in enumerate(questions, 1):
            total_questions += 1
            question_id = question.get('id', f'question_{total_questions}')
            
            logging.info(f"Processing question {total_questions}: {question_id}")
            
            # Get HTML text for this question (if available)
            html_text = html_texts.get(question_id)
            if html_text:
                logging.debug(f"Question {question_id}: Using HTML-extracted text")
            else:
                logging.debug(f"Question {question_id}: HTML text not found, using JSON prompt")
            
            # Check for gold_answer before mapping (most common failure reason)
            gold_answer = extract_gold_answer(question, section_type)
            if not gold_answer:
                failure_reasons['missing_gold_answer'].append(question_id)
                logging.warning(f"Question {question_id}: Failed to map to perturbation format - MISSING GOLD ANSWER")
                failed_questions += 1
                continue
            
            # Map to perturbation format
            question_data = map_to_perturbation_format(question, section_type, idx, html_text=html_text)
            if not question_data:
                logging.warning(f"Question {question_id}: Failed to map to perturbation format")
                failed_questions += 1
                continue
            
            # Format prompt
            prompt = format_prompt_for_question(question_data, k=k)
            if not prompt:
                logging.warning(f"Question {question_id}: Failed to format prompt")
                failed_questions += 1
                continue
            
            # Call API
            total_api_calls += 1
            response_text = call_openai_api(client, prompt, model=model, question_id=question_id)
            
            if response_text:
                successful_api_calls += 1
                # Parse response
                mappings = parse_perturbation_response(response_text, question_id)
                if not mappings:
                    failure_reasons['json_parse_error'].append(question_id)
                    logging.warning(f"Question {question_id}: Failed to parse API response - JSON PARSE ERROR")
                    failed_questions += 1
                    continue
                
                # Validate and select best perturbation
                validated_perturbation, failure_reason = select_best_perturbation(mappings, html_text or '', question_id)
                if validated_perturbation:
                    perturbations_dict[question_id] = [validated_perturbation]  # Store only validated one
                    successful_questions += 1
                    logging.info(f"Question {question_id}: Successfully generated and validated 1 perturbation (from {len(mappings)} generated)")
                else:
                    failed_questions += 1
                    if failure_reason:
                        # Map failure reason to tracking key
                        if failure_reason in failure_reasons:
                            failure_reasons[failure_reason].append(question_id)
                        else:
                            failure_reasons['no_valid_perturbations'].append(question_id)
                        logging.warning(f"Question {question_id}: All perturbations failed - REASON: {failure_reason.upper()}")
                    else:
                        failure_reasons['no_valid_perturbations'].append(question_id)
                        logging.warning(f"Question {question_id}: Generated {len(mappings)} perturbations but none validated")
            else:
                failed_api_calls += 1
                failed_questions += 1
                failure_reasons['api_call_failed'].append(question_id)
                logging.error(f"Question {question_id}: API call failed - API CALL FAILURE")
            
            # Rate limiting (small delay between calls)
            time.sleep(0.5)
    
    api_end_time = time.time()
    total_api_time = api_end_time - api_start_time
    
    # Merge perturbations into exam data
    total_perturbations = merge_perturbations_into_exam(exam_data, perturbations_dict)
    
    # Save output
    logging.info(f"Writing perturbed exam data to: {output_file}")
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(exam_data, f, indent=2, ensure_ascii=False)
        
        output_size = os.path.getsize(output_file)
        logging.info(f"Successfully wrote perturbed exam data ({output_size} bytes)")
    except Exception as e:
        logging.error(f"Error writing output file: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)
    
    # Final summary
    logging.info("=" * 80)
    logging.info("Perturbation Generation Complete")
    logging.info(f"Total questions: {total_questions}")
    logging.info(f"Successful questions: {successful_questions}")
    logging.info(f"Failed questions: {failed_questions}")
    logging.info("")
    logging.info("FAILURE BREAKDOWN:")
    logging.info(f"  Missing gold_answer: {len(failure_reasons['missing_gold_answer'])} question(s)")
    if failure_reasons['missing_gold_answer']:
        logging.info(f"    Question IDs: {', '.join(failure_reasons['missing_gold_answer'])}")
    logging.info(f"  JSON parse errors: {len(failure_reasons['json_parse_error'])} question(s)")
    if failure_reasons['json_parse_error']:
        logging.info(f"    Question IDs: {', '.join(failure_reasons['json_parse_error'])}")
    logging.info(f"  Substring mismatch: {len(failure_reasons['substring_mismatch'])} question(s)")
    if failure_reasons['substring_mismatch']:
        logging.info(f"    Question IDs: {', '.join(failure_reasons['substring_mismatch'])}")
    logging.info(f"  Position errors: {len(failure_reasons['position_error'])} question(s)")
    if failure_reasons['position_error']:
        logging.info(f"    Question IDs: {', '.join(failure_reasons['position_error'])}")
    logging.info(f"  Length violations: {len(failure_reasons['length_violation'])} question(s)")
    if failure_reasons['length_violation']:
        logging.info(f"    Question IDs: {', '.join(failure_reasons['length_violation'])}")
    logging.info(f"  Empty substring: {len(failure_reasons['empty_substring'])} question(s)")
    if failure_reasons['empty_substring']:
        logging.info(f"    Question IDs: {', '.join(failure_reasons['empty_substring'])}")
    logging.info(f"  API call failures: {len(failure_reasons['api_call_failed'])} question(s)")
    if failure_reasons['api_call_failed']:
        logging.info(f"    Question IDs: {', '.join(failure_reasons['api_call_failed'])}")
    logging.info(f"  No valid perturbations: {len(failure_reasons['no_valid_perturbations'])} question(s)")
    if failure_reasons['no_valid_perturbations']:
        logging.info(f"    Question IDs: {', '.join(failure_reasons['no_valid_perturbations'])}")
    logging.info("")
    logging.info(f"Total API calls: {total_api_calls}")
    logging.info(f"Successful API calls: {successful_api_calls}")
    logging.info(f"Failed API calls: {failed_api_calls}")
    logging.info(f"Total API time: {total_api_time:.2f} seconds")
    logging.info(f"Total perturbations generated: {total_perturbations}")
    logging.info(f"Average perturbations per successful question: {total_perturbations / successful_questions if successful_questions > 0 else 0:.2f}")
    logging.info(f"Output file: {output_file} ({output_size} bytes)")
    logging.info("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate perturbations for exam questions")
    parser.add_argument("input_file", help="Path to normalized exam JSON file")
    parser.add_argument("output_file", help="Path to output perturbed exam JSON file")
    parser.add_argument("--baseline-html", help="Path to baseline HTML file (for position calculation)")
    parser.add_argument("--api-key", required=False, help="OpenAI API key (or set OPENAI_API_KEY in .env or environment variable)")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)")
    parser.add_argument("--k", type=int, default=3, help="Number of perturbations per question (default: 3)")
    
    args = parser.parse_args()
    
    # Get API key from argument, .env file, or environment variable (in that priority order)
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        logging.error("OpenAI API key required. Provide via --api-key, set OPENAI_API_KEY in .env file, or set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    generate_perturbations(
        input_file=args.input_file,
        output_file=args.output_file,
        api_key=api_key,
        model=args.model,
        k=args.k,
        baseline_html=args.baseline_html
    )

