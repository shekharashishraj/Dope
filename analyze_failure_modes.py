#!/usr/bin/env python3
"""Analyze failure modes from DoPE evaluation results.

This script scans all detection_results.json files and categorizes failures
for qualitative analysis in the paper.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import sys


def load_all_detection_results(eval_dirs: List[Path]) -> List[Dict[str, Any]]:
    """Load all detection results from evaluation directories."""
    all_results = []
    
    for eval_dir in eval_dirs:
        if not eval_dir.exists():
            print(f"Warning: {eval_dir} does not exist, skipping", file=sys.stderr)
            continue
            
        for detection_file in eval_dir.rglob("detection_results.json"):
            try:
                with open(detection_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                    if isinstance(results, list):
                        for result in results:
                            result['_source_file'] = str(detection_file)
                            result['_eval_dir'] = str(eval_dir)
                            # Infer model from directory name
                            if 'gpt4o' in str(eval_dir).lower():
                                result['_model'] = 'gpt-4o'
                            elif 'gpt51' in str(eval_dir).lower() or 'gpt-5.1' in str(eval_dir).lower():
                                result['_model'] = 'gpt-5.1'
                            elif 'opus' in str(eval_dir).lower():
                                result['_model'] = 'claude-opus-4-5-20251101'
                            elif 'sonnet' in str(eval_dir).lower():
                                result['_model'] = 'claude-sonnet-4-5-20250929'
                            else:
                                result['_model'] = 'unknown'
                        all_results.extend(results)
            except Exception as e:
                print(f"Error loading {detection_file}: {e}", file=sys.stderr)
    
    return all_results


def load_perturbation_json(docid: str, variant: Optional[str], 
                          perturbation_base_dir: Path) -> Optional[Dict[str, Any]]:
    """Load prevention perturbation JSON for a docid and variant."""
    if variant is None:
        # ICW case - try without variant (ICW doesn't use variant in filename)
        # Actually, ICW might still have a variant, let's try both
        patterns = [
            f"{docid}_prevention_perturbation_*.json",
        ]
    else:
        patterns = [f"{docid}_prevention_perturbation_{variant}.json"]
    
    for pattern in patterns:
        for json_file in perturbation_base_dir.rglob(pattern):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {json_file}: {e}", file=sys.stderr)
    
    return None


def get_question_data(perturbation_data: Dict[str, Any], question_number: int) -> Optional[Dict[str, Any]]:
    """Extract question data from perturbation JSON."""
    questions = perturbation_data.get('questions', [])
    for q in questions:
        if q.get('question_number') == question_number:
            return q
    return None


def categorize_failure(result: Dict[str, Any], question_data: Optional[Dict[str, Any]] = None) -> Tuple[str, str, str]:
    """
    Categorize a failure into failure mode categories.
    
    Returns:
        Tuple of (category, subcategory, description)
    """
    prevention_success = result.get('prevention_success', False)
    refused = result.get('refused', False)
    detected = result.get('detected', False)
    question_type = result.get('question_type', '')
    ai_answer = result.get('ai_answer', '')
    gold_answer = result.get('gold_answer', '')
    target_wrong_answer = result.get('target_wrong_answer', '')
    reason = result.get('reason', '')
    method = result.get('method', '')
    model = result.get('_model', '')
    
    # Check for vision/image-based parsing (screenshot/OCR)
    vision_indicators = [
        'unreadable', 'encrypted', 'unable to read', 'cannot read', 
        'screenshot', 'image', 'OCR', 'vision', 'unreadable text',
        'due to encrypted', 'text is not readable'
    ]
    ai_answer_lower = (ai_answer or '').lower()
    is_vision_parsing = any(indicator in ai_answer_lower for indicator in vision_indicators)
    
    # Check for memorization (perturbation detected but gold answer given)
    is_memorization = False
    if detected and ai_answer and gold_answer:
        # Model saw perturbation (detected=True) but still gave gold answer
        ai_norm = str(ai_answer).lower().strip()
        gold_norm = str(gold_answer).lower().strip()
        if question_type == 'MCQ':
            # Check if AI answer matches gold (option letter or full answer)
            if gold_norm in ai_norm or ai_norm == gold_norm:
                is_memorization = True
        elif question_type == 'TF':
            if gold_norm in ai_norm:
                is_memorization = True
    
    # Vision/image-based parsing (screenshot) - both prevention and detection
    if is_vision_parsing:
        if 'claude' in model.lower() or 'opus' in model.lower() or 'sonnet' in model.lower():
            if not prevention_success:
                return ("prevention", "vision_parsing_claude",
                       f"Claude model used vision/OCR parsing - answered despite perturbation: {ai_answer[:100]}")
            else:
                return ("detection", "vision_parsing_claude",
                       f"Claude model used vision/OCR parsing - detected but vision-based")
        else:
            if not prevention_success:
                return ("prevention", "vision_parsing_general",
                       f"Model used vision/OCR parsing - answered despite perturbation: {ai_answer[:100]}")
            else:
                return ("detection", "vision_parsing_general",
                       f"Model used vision/OCR parsing - detected but vision-based")
    
    # Prevention failures (prevention_success = False)
    if not prevention_success:
        if refused:
            # This shouldn't happen, but handle it
            return ("prevention", "unexpected_refusal", "Model refused but marked as prevention failure")
        
        # Model answered instead of refusing
        if not detected:
            # Model answered correctly - perturbation too weak
            if question_type == 'TF':
                return ("prevention", "weak_perturbation_tf", 
                       f"TF: Model answered {gold_answer} correctly despite perturbation")
            elif question_type == 'MCQ':
                return ("prevention", "weak_perturbation_mcq",
                       f"MCQ: Model answered {gold_answer} correctly despite perturbation")
            elif question_type == 'LONG':
                return ("prevention", "weak_perturbation_long",
                       "LONG: Model answered correctly despite perturbation")
            else:
                return ("prevention", "weak_perturbation_unknown",
                       f"Model answered correctly despite perturbation")
        
        else:
            # Model answered incorrectly - perturbation worked but didn't cause refusal
            if is_memorization:
                # Perturbation detected but model memorized gold answer
                return ("prevention", "perturbation_detected_memorization",
                       f"Perturbation detected but model memorized gold answer {gold_answer} (AI: {ai_answer})")
            elif method == 'icw':
                return ("prevention", "icw_ignored",
                       "ICW prompt ignored - model answered instead of refusing")
            else:
                return ("prevention", "perturbation_detected_but_answered",
                       f"Perturbation detected (wrong answer: {ai_answer}) but model didn't refuse")
    
    # Detection failures (for detection mode, but we're in prevention mode)
    # These would be cases where we can't detect misuse
    if not detected and not refused:
        if is_memorization:
            # Weak perturbation but model memorized answer
            if question_type == 'TF':
                return ("detection", "weak_perturbation_memorization_tf",
                       f"TF: Weak perturbation, model memorized gold answer {gold_answer}")
            elif question_type == 'MCQ':
                return ("detection", "weak_perturbation_memorization_mcq",
                       f"MCQ: Weak perturbation, model memorized gold answer {gold_answer}")
            else:
                return ("detection", "weak_perturbation_memorization",
                       f"Weak perturbation, model memorized gold answer {gold_answer}")
        elif question_type == 'TF':
            ai_norm = ai_answer.lower().strip()
            gold_norm = gold_answer.lower().strip()
            if gold_norm in ai_norm:
                return ("detection", "false_negative_tf",
                       f"TF: Model answered {gold_answer} correctly - perturbation didn't flip answer")
        elif question_type == 'MCQ':
            if ai_answer == gold_answer or gold_answer in ai_answer:
                return ("detection", "false_negative_mcq",
                       f"MCQ: Model answered {gold_answer} correctly - perturbation didn't shift answer")
    
    # Parsing failures
    parsing_method = result.get('parsing_method', '')
    if parsing_method == 'regex' and not detected:
        return ("detection", "parsing_failure",
               "LLM judge and JSON mode failed, fell back to regex")
    
    # Unknown failure
    return ("unknown", "unknown", f"Unknown failure: {reason}")


def extract_failure_examples(
    all_results: List[Dict[str, Any]],
    perturbation_base_dir: Path,
    max_examples_per_category: int = 5
) -> Dict[str, List[Dict[str, Any]]]:
    """Extract representative examples for each failure category."""
    categorized = defaultdict(list)
    
    # Build index of perturbation JSONs
    perturbation_index = {}
    for json_file in perturbation_base_dir.rglob("*_prevention_perturbation_*.json"):
        name = json_file.name
        parts = name.split("_prevention_perturbation_")
        if len(parts) == 2:
            docid = parts[0]
            variant = parts[1].replace(".json", "")
            key = f"{docid}::{variant}"
            perturbation_index[key] = json_file
    
    for result in all_results:
        # Only process failures
        if result.get('prevention_success', False):
            continue  # Skip successes
        
        category, subcategory, description = categorize_failure(result)
        
        # Load perturbation data if available
        docid = result.get('docid', '')
        variant = result.get('variant')
        question_number = result.get('question_number')
        
        question_data = None
        perturbation_details = None
        
        if docid:
            # Try to load perturbation data
            pert_data = load_perturbation_json(docid, variant, perturbation_base_dir)
            if pert_data:
                question_data = get_question_data(pert_data, question_number)
                if question_data:
                    perturbations = question_data.get('perturbations', [])
                    if perturbations:
                        perturbation_details = perturbations[0]  # Get first perturbation
        
        # Build example
        example = {
            'category': category,
            'subcategory': subcategory,
            'description': description,
            'docid': docid,
            'question_number': question_number,
            'question_type': result.get('question_type', ''),
            'method': result.get('method', ''),
            'variant': variant,
            'model': result.get('_model', 'unknown'),
            'ai_answer': result.get('ai_answer', ''),
            'gold_answer': gold_answer if (gold_answer := result.get('gold_answer')) else '',
            'target_wrong_answer': target_wrong_answer if (target_wrong_answer := result.get('target_wrong_answer')) else '',
            'reason': result.get('reason', ''),
            'prevention_reason': result.get('prevention_reason', ''),
            'parsing_method': result.get('parsing_method', ''),
            'source_file': result.get('_source_file', ''),
        }
        
        # Add question and perturbation details if available
        if question_data:
            example['original_question'] = question_data.get('latex_stem_text') or question_data.get('stem_text', '')
            example['gold_answer_full'] = question_data.get('gold_answer', '')
        
        if perturbation_details:
            example['perturbation'] = {
                'original_substring': perturbation_details.get('original_substring', ''),
                'replacement_substring': perturbation_details.get('replacement_substring', ''),
                'start_pos': perturbation_details.get('start_pos'),
                'end_pos': perturbation_details.get('end_pos'),
            }
        
        categorized[f"{category}::{subcategory}"].append(example)
    
    # Limit examples per category
    limited = {}
    for key, examples in categorized.items():
        limited[key] = examples[:max_examples_per_category]
    
    return limited


def generate_statistics(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate statistics on failure frequency."""
    stats = {
        'total_results': len(all_results),
        'prevention_successes': sum(1 for r in all_results if r.get('prevention_success', False)),
        'prevention_failures': sum(1 for r in all_results if not r.get('prevention_success', False)),
        'by_category': defaultdict(int),
        'by_model': defaultdict(lambda: {'success': 0, 'failure': 0}),
        'by_method': defaultdict(lambda: {'success': 0, 'failure': 0}),
        'by_question_type': defaultdict(lambda: {'success': 0, 'failure': 0}),
    }
    
    for result in all_results:
        model = result.get('_model', 'unknown')
        method = result.get('method', 'unknown')
        question_type = result.get('question_type', 'unknown')
        prevention_success = result.get('prevention_success', False)
        
        category, subcategory, _ = categorize_failure(result)
        stats['by_category'][f"{category}::{subcategory}"] += 1
        
        if prevention_success:
            stats['by_model'][model]['success'] += 1
            stats['by_method'][method]['success'] += 1
            stats['by_question_type'][question_type]['success'] += 1
        else:
            stats['by_model'][model]['failure'] += 1
            stats['by_method'][method]['failure'] += 1
            stats['by_question_type'][question_type]['failure'] += 1
    
    return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze DoPE failure modes")
    parser.add_argument('--eval-dirs', nargs='+', required=True,
                       help='Evaluation directories containing detection_results.json files')
    parser.add_argument('--perturbation-dir', required=True,
                       help='Base directory containing prevention perturbation JSONs')
    parser.add_argument('--output-json', default='failure_modes_analysis.json',
                       help='Output JSON file for structured data')
    parser.add_argument('--max-examples', type=int, default=5,
                       help='Maximum examples per category')
    
    args = parser.parse_args()
    
    eval_dirs = [Path(d) for d in args.eval_dirs]
    perturbation_base_dir = Path(args.perturbation_dir)
    
    print("Loading detection results...")
    all_results = load_all_detection_results(eval_dirs)
    print(f"Loaded {len(all_results)} results")
    
    print("Extracting failure examples...")
    examples = extract_failure_examples(all_results, perturbation_base_dir, args.max_examples)
    print(f"Extracted examples for {len(examples)} categories")
    
    print("Generating statistics...")
    stats = generate_statistics(all_results)
    
    output = {
        'statistics': stats,
        'examples': examples,
    }
    
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Analysis complete. Results saved to {args.output_json}")
    print(f"\nSummary:")
    print(f"  Total results: {stats['total_results']}")
    print(f"  Prevention successes: {stats['prevention_successes']}")
    print(f"  Prevention failures: {stats['prevention_failures']}")
    print(f"  Categories found: {len(stats['by_category'])}")


if __name__ == '__main__':
    main()
