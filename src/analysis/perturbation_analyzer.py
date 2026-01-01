"""Analyze perturbation failures from detection results."""
import argparse
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


# Tier 1 directional inversion patterns
TIER_1_PATTERNS = [
    (r'\b(increases?|increasing)\b', r'\b(decreases?|decreasing)\b', 'directional_inversion'),
    (r'\b(decreases?|decreasing)\b', r'\b(increases?|increasing)\b', 'directional_inversion'),
    (r'\b(greater|more|higher|larger)\b', r'\b(less|fewer|lower|smaller)\b', 'directional_inversion'),
    (r'\b(less|fewer|lower|smaller)\b', r'\b(greater|more|higher|larger)\b', 'directional_inversion'),
    (r'\b(positive|positively)\b', r'\b(negative|negatively)\b', 'directional_inversion'),
    (r'\b(negative|negatively)\b', r'\b(positive|positively)\b', 'directional_inversion'),
    (r'\b(before|prior to|earlier)\b', r'\b(after|following|later)\b', 'directional_inversion'),
    (r'\b(after|following|later)\b', r'\b(before|prior to|earlier)\b', 'directional_inversion'),
    (r'\b(maximum|max)\b', r'\b(minimum|min)\b', 'directional_inversion'),
    (r'\b(minimum|min)\b', r'\b(maximum|max)\b', 'directional_inversion'),
    (r'\b(clockwise)\b', r'\b(counterclockwise)\b', 'directional_inversion'),
    (r'\b(counterclockwise)\b', r'\b(clockwise)\b', 'directional_inversion'),
    (r'\b(exothermic)\b', r'\b(endothermic)\b', 'property_swap'),
    (r'\b(endothermic)\b', r'\b(exothermic)\b', 'property_swap'),
    (r'\b(acidic)\b', r'\b(basic|alkaline)\b', 'property_swap'),
    (r'\b(basic|alkaline)\b', r'\b(acidic)\b', 'property_swap'),
    (r'\b(conductor)\b', r'\b(insulator)\b', 'property_swap'),
    (r'\b(insulator)\b', r'\b(conductor)\b', 'property_swap'),
    (r'\b(soluble)\b', r'\b(insoluble)\b', 'property_swap'),
    (r'\b(insoluble)\b', r'\b(soluble)\b', 'property_swap'),
    (r'\b(dominant)\b', r'\b(recessive)\b', 'property_swap'),
    (r'\b(recessive)\b', r'\b(dominant)\b', 'property_swap'),
]

# Negation patterns (prohibited)
NEGATION_PATTERNS = [
    r'\bnot\b',
    r'\bnever\b',
    r'\bno\b',
    r'\bcannot\b',
    r'\bcan\'t\b',
    r'\bwon\'t\b',
    r'\bun-',
    r'\bnon-',
    r'\bin-',
    r'\bdis-',
]


def classify_perturbation_pattern(perturbation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify perturbation pattern and estimate Tier level.
    
    Args:
        perturbation: Perturbation mapping dict with original_substring and replacement_substring
    
    Returns:
        Dict with tier_estimate, technique, violates_constraints, strength_issue
    """
    original = perturbation.get('original_substring', '').lower()
    replacement = perturbation.get('replacement_substring', '').lower()
    
    # Check for negation violations
    violates_constraints = False
    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, replacement, re.IGNORECASE):
            violates_constraints = True
            break
    
    # Check length constraint
    if len(replacement) > len(original):
        violates_constraints = True
    
    # Check for Tier 1 patterns
    tier_estimate = "Tier 4"
    technique = "entity_substitution"
    strength_issue = None
    
    for orig_pattern, repl_pattern, tech in TIER_1_PATTERNS:
        if re.search(orig_pattern, original, re.IGNORECASE) and re.search(repl_pattern, replacement, re.IGNORECASE):
            tier_estimate = "Tier 1"
            technique = tech
            break
    
    # Check for Tier 2 (property swaps not in Tier 1)
    if tier_estimate == "Tier 4":
        property_swaps = [
            ('oxidized', 'reduced'), ('reduced', 'oxidized'),
            ('aerobic', 'anaerobic'), ('anaerobic', 'aerobic'),
            ('active', 'inactive'), ('inactive', 'active'),
        ]
        for prop1, prop2 in property_swaps:
            if prop1 in original and prop2 in replacement:
                tier_estimate = "Tier 2"
                technique = "property_swap"
                break
    
    # Check for Tier 3 (quantifier modifications)
    if tier_estimate == "Tier 4":
        quantifier_pairs = [
            ('always', 'sometimes'), ('always', 'usually'),
            ('all', 'some'), ('all', 'most'),
            ('never', 'rarely'), ('every', 'most'),
        ]
        for q1, q2 in quantifier_pairs:
            if q1 in original and q2 in replacement:
                tier_estimate = "Tier 3"
                technique = "quantifier_modification"
                strength_issue = "too_subtle"
                break
    
    # Assess strength
    if tier_estimate in ["Tier 3", "Tier 4"]:
        strength_issue = "too_weak"
    elif tier_estimate == "Tier 1" and not violates_constraints:
        strength_issue = None  # Strong perturbation
    elif violates_constraints:
        strength_issue = "violates_constraints"
    
    return {
        "tier_estimate": tier_estimate,
        "technique": technique,
        "violates_constraints": violates_constraints,
        "strength_issue": strength_issue
    }


def identify_failure_reason(
    result: Dict[str, Any],
    question: Dict[str, Any]
) -> Tuple[str, str]:
    """
    Identify why a detection failed.
    
    Args:
        result: Detection result dict
        question: Question dict with gold_answer and target_wrong_answer
    
    Returns:
        Tuple of (failure_reason, description)
    """
    if result.get('refused', False):
        return ("refused", "AI refused to answer")
    
    detected = result.get('detected', False)
    question_type = result.get('question_type', '')
    ai_answer = result.get('ai_answer', '')
    gold_answer = question.get('gold_answer', '')
    target_wrong_answer = question.get('target_wrong_answer', '')
    
    if not detected:
        if question_type == "TF":
            # Check if AI answered gold instead of target
            ai_normalized = ai_answer.lower().strip()
            gold_normalized = gold_answer.lower().strip()
            target_normalized = target_wrong_answer.lower().strip() if target_wrong_answer else ''
            
            if 'true' in ai_normalized or 'false' in ai_normalized:
                if gold_normalized in ai_normalized and target_normalized not in ai_normalized:
                    return ("perturbation_did_not_flip", f"AI answered {gold_answer} instead of {target_wrong_answer}")
            
            return ("perturbation_did_not_flip", "Perturbation did not cause AI to flip answer")
        
        elif question_type == "MCQ":
            # Check if AI answered gold instead of target
            if ai_answer == gold_answer or gold_answer in ai_answer:
                return ("perturbation_did_not_shift", f"AI answered {gold_answer} instead of {target_wrong_answer}")
            return ("perturbation_did_not_shift", "Perturbation did not cause answer shift")
        
        elif question_type == "LONG":
            # Check similarity (basic heuristic)
            return ("perturbation_too_similar", "AI answer too similar to gold answer")
    
    return ("unknown", "Unknown failure reason")


def suggest_improvement(failure_data: Dict[str, Any]) -> str:
    """
    Suggest improvement for a failed perturbation.
    
    Args:
        failure_data: Dict with failure analysis data
    
    Returns:
        Improvement suggestion string
    """
    pattern = failure_data.get('pattern_analysis', {})
    tier = pattern.get('tier_estimate', 'Tier 4')
    technique = pattern.get('technique', '')
    violates = pattern.get('violates_constraints', False)
    strength = pattern.get('strength_issue', '')
    question_type = failure_data.get('question_type', '')
    
    suggestions = []
    
    if violates:
        suggestions.append("Remove negation words or fix length constraint violation")
    
    if tier == "Tier 3":
        suggestions.append("Use Tier 1 directional inversion instead (e.g., 'increases' ↔ 'decreases', 'greater' ↔ 'less')")
    
    if tier == "Tier 4":
        suggestions.append("Use Tier 1 directional inversion or Tier 2 property swap instead")
    
    if strength == "too_subtle":
        suggestions.append("Make perturbation more substantial - use clear directional inversions")
    
    if question_type == "TF" and tier != "Tier 1":
        suggestions.append("For TF questions, prioritize Tier 1 techniques (directional inversions) for reliable truth flips")
    
    if not suggestions:
        suggestions.append("Ensure perturbation creates unambiguous factual change")
    
    return "; ".join(suggestions)


def find_perturbation_for_question(
    question_number: int,
    perturbation_json: Path,
    method: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Find the perturbation that was applied to a question.
    
    Args:
        question_number: Question number
        perturbation_json: Path to perturbation JSON file
        method: Optional method name to filter by
    
    Returns:
        Perturbation mapping dict or None
    """
    try:
        with open(perturbation_json, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
        
        # Find question
        questions = doc_data.get('questions', [])
        for question in questions:
            if question.get('question_number') == question_number:
                perturbations = question.get('perturbations', [])
                if perturbations:
                    # If method specified, try to match (though perturbation JSON doesn't store method)
                    # For now, return first perturbation
                    return perturbations[0]
                break
    except Exception as e:
        logger.warning(f"Error reading perturbation JSON {perturbation_json}: {e}")
    
    return None


def analyze_failed_perturbations(
    detection_dir: Path,
    perturbation_base_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Analyze failed perturbations from detection results.
    
    Args:
        detection_dir: Directory containing detection results (output_detection/<timestamp>)
        perturbation_base_dir: Base directory for perturbation JSONs (default: output_perturbation)
    
    Returns:
        Analysis results dict
    """
    if perturbation_base_dir is None:
        perturbation_base_dir = Path("output_perturbation")
    
    failed_perturbations = []
    summary_stats = {
        "total_failures": 0,
        "by_question_type": defaultdict(int),
        "by_failure_reason": defaultdict(int),
        "by_perturbation_pattern": defaultdict(int),
        "by_tier": defaultdict(int),
    }
    
    # Find all detection result files
    detection_results_files = list(detection_dir.rglob("detection_results.json"))
    
    for results_file in detection_results_files:
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                detection_data = json.load(f)
            
            document_id = detection_data.get('document_id', '')
            pdf_path = detection_data.get('pdf_path', '')
            results = detection_data.get('results', [])
            
            # Extract perturbation JSON path from PDF path
            pdf_path_obj = Path(pdf_path) if pdf_path else None
            perturbation_json = None
            
            if pdf_path_obj:
                # Try to find corresponding perturbation JSON
                pdf_parts = pdf_path_obj.parts
                if "output_attacked_pdfs" in pdf_parts:
                    try:
                        pdf_idx = pdf_parts.index("output_attacked_pdfs")
                        timestamp = pdf_parts[pdf_idx + 1]
                        domain = pdf_parts[pdf_idx + 2]
                        level = pdf_parts[pdf_idx + 3]
                        doc_name = pdf_parts[pdf_idx + 4]
                        
                        # Try to find JSON
                        candidate = perturbation_base_dir / timestamp / domain.lower() / level.lower() / doc_name / f"{doc_name}_perturbation.json"
                        if not candidate.exists():
                            # Search all timestamps
                            for ts_dir in perturbation_base_dir.iterdir():
                                if ts_dir.is_dir():
                                    candidate = ts_dir / domain.lower() / level.lower() / doc_name / f"{doc_name}_perturbation.json"
                                    if candidate.exists():
                                        break
                        
                        if candidate.exists():
                            perturbation_json = candidate
                    except (IndexError, ValueError) as e:
                        logger.warning(f"Could not parse PDF path {pdf_path}: {e}")
            
            # Also try to load full document to get question details
            doc_questions = {}
            if perturbation_json and perturbation_json.exists():
                try:
                    with open(perturbation_json, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                    for q in doc_data.get('questions', []):
                        doc_questions[q.get('question_number')] = q
                except Exception as e:
                    logger.warning(f"Error loading document data: {e}")
            
            # Analyze each failed result
            for result in results:
                if not result.get('detected', False) and not result.get('refused', False):
                    # This is a failure
                    question_number = result.get('question_number')
                    question_type = result.get('question_type', '')
                    
                    # Get question details
                    question = doc_questions.get(question_number, {})
                    
                    # Find perturbation
                    perturbation = None
                    if perturbation_json:
                        perturbation = find_perturbation_for_question(question_number, perturbation_json)
                    
                    # Identify failure reason
                    failure_reason, failure_desc = identify_failure_reason(result, question)
                    
                    # Classify pattern
                    pattern_analysis = {}
                    if perturbation:
                        pattern_analysis = classify_perturbation_pattern(perturbation)
                    
                    # Suggest improvement
                    failure_data_for_suggestion = {
                        'pattern_analysis': pattern_analysis,
                        'question_type': question_type
                    }
                    suggestion = suggest_improvement(failure_data_for_suggestion)
                    
                    # Build failure record
                    failure_record = {
                        "document_id": document_id,
                        "question_number": question_number,
                        "question_type": question_type,
                        "gold_answer": result.get('gold_answer', ''),
                        "target_wrong_answer": result.get('target_wrong_answer', ''),
                        "ai_answer": result.get('ai_answer', ''),
                        "perturbation": {
                            "original_substring": perturbation.get('original_substring', '') if perturbation else '',
                            "replacement_substring": perturbation.get('replacement_substring', '') if perturbation else '',
                            "reasoning": perturbation.get('reasoning', '') if perturbation else '',
                            "verification": perturbation.get('verification', '') if perturbation else '',
                        } if perturbation else None,
                        "failure_reason": failure_reason,
                        "failure_description": failure_desc,
                        "pattern_analysis": pattern_analysis,
                        "suggested_improvement": suggestion
                    }
                    
                    failed_perturbations.append(failure_record)
                    
                    # Update summary stats
                    summary_stats["total_failures"] += 1
                    summary_stats["by_question_type"][question_type] += 1
                    summary_stats["by_failure_reason"][failure_reason] += 1
                    if pattern_analysis:
                        summary_stats["by_perturbation_pattern"][pattern_analysis.get('technique', 'unknown')] += 1
                        summary_stats["by_tier"][pattern_analysis.get('tier_estimate', 'unknown')] += 1
        
        except Exception as e:
            logger.error(f"Error processing {results_file}: {e}")
            continue
    
    # Convert defaultdicts to regular dicts for JSON serialization
    summary = {
        "total_failures": summary_stats["total_failures"],
        "by_question_type": dict(summary_stats["by_question_type"]),
        "by_failure_reason": dict(summary_stats["by_failure_reason"]),
        "by_perturbation_pattern": dict(summary_stats["by_perturbation_pattern"]),
        "by_tier": dict(summary_stats["by_tier"]),
    }
    
    return {
        "summary": summary,
        "failed_perturbations": failed_perturbations
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze perturbation failures from detection results"
    )
    parser.add_argument(
        "--detection-dir",
        type=str,
        required=True,
        help="Directory containing detection results (output_detection/<timestamp>)"
    )
    parser.add_argument(
        "--perturbation-dir",
        type=str,
        default="output_perturbation",
        help="Base directory for perturbation JSONs (default: output_perturbation)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file (default: <detection_dir>/perturbation_analysis.json)"
    )
    
    args = parser.parse_args()
    
    detection_dir = Path(args.detection_dir)
    perturbation_dir = Path(args.perturbation_dir)
    
    if not detection_dir.exists():
        logger.error(f"Detection directory does not exist: {detection_dir}")
        return
    
    logger.info(f"Analyzing failures in {detection_dir}")
    
    # Run analysis
    analysis_results = analyze_failed_perturbations(detection_dir, perturbation_dir)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = detection_dir / "perturbation_analysis.json"
    
    # Write results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Analysis complete. Results written to {output_path}")
    logger.info(f"Total failures: {analysis_results['summary']['total_failures']}")
    logger.info(f"By question type: {analysis_results['summary']['by_question_type']}")
    logger.info(f"By failure reason: {analysis_results['summary']['by_failure_reason']}")
    logger.info(f"By tier: {analysis_results['summary']['by_tier']}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()

