#!/usr/bin/env python3
"""Consolidate refusal rates with confidence intervals from all prevention evaluations."""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import math


def wilson_confidence_interval(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    """
    Calculate Wilson score confidence interval for binomial proportion.
    
    Args:
        successes: Number of successes (refusals)
        total: Total number of trials
        confidence: Confidence level (default 0.95 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound) as proportions (0-1)
    """
    if total == 0:
        return (0.0, 0.0)
    
    z = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
    p = successes / total
    
    denominator = 1 + (z**2 / total)
    center = (p + (z**2 / (2 * total))) / denominator
    margin = (z / denominator) * math.sqrt((p * (1 - p) / total) + (z**2 / (4 * total**2)))
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)


def load_all_detection_results(eval_dirs: Dict[str, Path]) -> Dict[str, List[Dict[str, Any]]]:
    """Load all detection_results.json files from evaluation directories."""
    all_results = {}
    
    for model_name, eval_dir in eval_dirs.items():
        if not eval_dir.exists():
            print(f"Warning: Evaluation directory not found: {eval_dir}")
            continue
        
        results = []
        detection_files = list(eval_dir.rglob("detection_results.json"))
        print(f"{model_name}: Found {len(detection_files)} detection_results.json files")
        
        for result_file in detection_files:
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    file_results = json.load(f)
                    if isinstance(file_results, list):
                        results.extend(file_results)
                    else:
                        results.append(file_results)
            except Exception as e:
                print(f"Error loading {result_file}: {e}", file=sys.stderr)
                continue
        
        all_results[model_name] = results
        print(f"{model_name}: Loaded {len(results)} total results")
    
    return all_results


def extract_domain_from_docid(docid: str) -> str:
    """Extract domain from docid (e.g., 'biology_graduate_doc_01' -> 'biology')."""
    parts = docid.split('_')
    # Domain is everything before the level (graduate/undergraduate/k-12)
    level_keywords = ['graduate', 'undergraduate', 'k-12']
    domain_parts = []
    for part in parts:
        if part in level_keywords or (part == 'k' and len(parts) > parts.index(part) + 1 and parts[parts.index(part) + 1] == '12'):
            break
        domain_parts.append(part)
    return '_'.join(domain_parts) if domain_parts else 'unknown'


def calculate_refusal_rates_by_dimensions(all_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Calculate refusal rates with confidence intervals broken down by:
    - Model
    - Domain
    - Question type
    - Attack type (method)
    - Variant
    """
    # Structure: model -> domain -> question_type -> method -> variant -> stats
    def make_nested_dict():
        return defaultdict(lambda: {
            'refused': 0,
            'total': 0,
            'results': []
        })
    
    breakdown = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(make_nested_dict))))
    
    # Load all results
    for model_name, results in all_results.items():
        for result in results:
            # Extract dimensions
            domain = extract_domain_from_docid(result.get('docid', 'unknown'))
            question_type = result.get('question_type', 'UNKNOWN')
            method = result.get('method', 'unknown')
            variant = result.get('variant') or 'none'  # Handle None for ICW
            refused = result.get('refused', False)
            
            # Count
            breakdown[model_name][domain][question_type][method][variant]['total'] += 1
            if refused:
                breakdown[model_name][domain][question_type][method][variant]['refused'] += 1
            breakdown[model_name][domain][question_type][method][variant]['results'].append(result)
    
    # Calculate rates and confidence intervals
    consolidated = {}
    
    for model_name in sorted(breakdown.keys()):
        model_data = {}
        
        for domain in sorted(breakdown[model_name].keys()):
            domain_data = {}
            
            for question_type in sorted(breakdown[model_name][domain].keys()):
                type_data = {}
                
                for method in sorted(breakdown[model_name][domain][question_type].keys()):
                    method_data = {}
                    
                    for variant in sorted(breakdown[model_name][domain][question_type][method].keys()):
                        stats = breakdown[model_name][domain][question_type][method][variant]
                        total = stats['total']
                        refused = stats['refused']
                        
                        if total == 0:
                            continue
                        
                        refusal_rate = (refused / total) * 100
                        ci_lower, ci_upper = wilson_confidence_interval(refused, total, 0.95)
                        
                        method_data[variant] = {
                            'total_questions': total,
                            'refused_count': refused,
                            'answered_count': total - refused,
                            'refusal_rate': round(refusal_rate, 2),
                            'refusal_rate_proportion': round(refused / total, 4),
                            'confidence_interval_95': {
                                'lower': round(ci_lower * 100, 2),
                                'upper': round(ci_upper * 100, 2),
                                'lower_proportion': round(ci_lower, 4),
                                'upper_proportion': round(ci_upper, 4)
                            }
                        }
                    
                    if method_data:
                        type_data[method] = method_data
                
                if type_data:
                    domain_data[question_type] = type_data
            
            if domain_data:
                model_data[domain] = domain_data
        
        if model_data:
            consolidated[model_name] = model_data
    
    return consolidated


def calculate_aggregate_statistics(all_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Calculate overall statistics across all models."""
    overall_stats = {}
    
    for model_name, results in all_results.items():
        total = len(results)
        refused = sum(1 for r in results if r.get('refused', False))
        
        if total == 0:
            continue
        
        refusal_rate = (refused / total) * 100
        ci_lower, ci_upper = wilson_confidence_interval(refused, total, 0.95)
        
        overall_stats[model_name] = {
            'total_questions': total,
            'refused_count': refused,
            'answered_count': total - refused,
            'refusal_rate': round(refusal_rate, 2),
            'refusal_rate_proportion': round(refused / total, 4),
            'confidence_interval_95': {
                'lower': round(ci_lower * 100, 2),
                'upper': round(ci_upper * 100, 2),
                'lower_proportion': round(ci_lower, 4),
                'upper_proportion': round(ci_upper, 4)
            }
        }
    
    return overall_stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Consolidate refusal rates from prevention evaluations")
    parser.add_argument(
        "--output",
        type=str,
        default="prevention_refusal_rates_consolidated.json",
        help="Output JSON file (default: prevention_refusal_rates_consolidated.json)"
    )
    
    args = parser.parse_args()
    
    # Define evaluation directories
    eval_dirs = {
        'gpt-4o': Path('output_prevention_eval_gpt4o_full_all_parallel'),
        'gpt-5.1': Path('output_prevention_eval_gpt51_full_all_parallel'),
        'claude-opus-4-5': Path('output_prevention_eval_opus_limited'),
        'claude-sonnet-4-5': Path('output_prevention_eval_sonnet_limited')
    }
    
    print("Loading detection results from all evaluation directories...")
    all_results = load_all_detection_results(eval_dirs)
    
    if not all_results:
        print("Error: No results found in any evaluation directory!")
        sys.exit(1)
    
    print("\nCalculating refusal rates with confidence intervals...")
    breakdown = calculate_refusal_rates_by_dimensions(all_results)
    overall_stats = calculate_aggregate_statistics(all_results)
    
    # Create consolidated output
    consolidated = {
        'metadata': {
            'description': 'Refusal rates with 95% confidence intervals from prevention evaluations',
            'breakdown_dimensions': ['model', 'domain', 'question_type', 'attack_type', 'variant'],
            'confidence_level': 0.95,
            'models': list(eval_dirs.keys()),
            'total_models': len(eval_dirs)
        },
        'overall_statistics': overall_stats,
        'breakdown': breakdown
    }
    
    # Save to JSON
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"CONSOLIDATED REFUSAL RATES")
    print(f"{'='*80}\n")
    
    print(f"Overall Statistics by Model:")
    for model_name, stats in sorted(overall_stats.items()):
        print(f"\n  {model_name}:")
        print(f"    Total Questions: {stats['total_questions']}")
        print(f"    Refused: {stats['refused_count']} ({stats['refusal_rate']:.2f}%)")
        print(f"    Answered: {stats['answered_count']}")
        print(f"    95% CI: [{stats['confidence_interval_95']['lower']:.2f}%, {stats['confidence_interval_95']['upper']:.2f}%]")
    
    print(f"\n{'='*80}")
    print(f"✓ Results saved to {output_path}")
    print(f"{'='*80}\n")
    
    # Print sample breakdown
    print("Sample breakdown (first model, first domain, first question type):")
    for model_name in sorted(breakdown.keys()):
        model_data = breakdown[model_name]
        if model_data:
            first_domain = sorted(model_data.keys())[0]
            domain_data = model_data[first_domain]
            if domain_data:
                first_qtype = sorted(domain_data.keys())[0]
                type_data = domain_data[first_qtype]
                if type_data:
                    first_method = sorted(type_data.keys())[0]
                    method_data = type_data[first_method]
                    print(f"\n  {model_name} / {first_domain} / {first_qtype} / {first_method}:")
                    for variant, stats in sorted(method_data.items()):
                        print(f"    {variant}: {stats['refusal_rate']:.2f}% "
                              f"[{stats['confidence_interval_95']['lower']:.2f}%, "
                              f"{stats['confidence_interval_95']['upper']:.2f}%] "
                              f"(n={stats['total_questions']})")
                    break
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
