#!/usr/bin/env python3
"""Extract refusal rates by attack type with question type breakdowns."""
import json
import sys
from pathlib import Path
from collections import defaultdict
from math import sqrt


def wilson_confidence_interval(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Wilson score confidence interval for binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    
    z = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
    p = successes / total
    
    denominator = 1 + (z**2 / total)
    center = (p + (z**2 / (2 * total))) / denominator
    margin = (z / denominator) * sqrt((p * (1 - p) / total) + (z**2 / (4 * total**2)))
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)


def aggregate_by_attack_and_qtype(breakdown_data: dict) -> dict:
    """Aggregate refusal rates by attack type (method+variant) and question type."""
    # Structure: attack_type -> question_type -> counts
    by_attack_qtype = defaultdict(lambda: defaultdict(lambda: {'refused': 0, 'total': 0}))
    
    for domain_data in breakdown_data.values():
        for qtype, type_data in domain_data.items():
            for method, method_data in type_data.items():
                for variant, variant_data in method_data.items():
                    # Create attack type key: method_variant or just method for ICW
                    if method == 'icw':
                        attack_key = 'icw'
                    else:
                        attack_key = f"{method}_{variant}"
                    
                    by_attack_qtype[attack_key][qtype]['refused'] += variant_data['refused_count']
                    by_attack_qtype[attack_key][qtype]['total'] += variant_data['total_questions']
    
    # Calculate rates and CIs
    result = {}
    for attack_type in sorted(by_attack_qtype.keys()):
        attack_result = {}
        for qtype in sorted(by_attack_qtype[attack_type].keys()):
            counts = by_attack_qtype[attack_type][qtype]
            if counts['total'] == 0:
                continue
            
            refusal_rate = (counts['refused'] / counts['total']) * 100
            ci_lower, ci_upper = wilson_confidence_interval(counts['refused'], counts['total'], 0.95)
            
            attack_result[qtype] = {
                'refusal_rate': round(refusal_rate, 2),
                'confidence_interval_95': {
                    'lower': round(ci_lower * 100, 2),
                    'upper': round(ci_upper * 100, 2)
                },
                'total_questions': counts['total'],
                'refused_count': counts['refused'],
                'answered_count': counts['total'] - counts['refused']
            }
        
        if attack_result:
            result[attack_type] = attack_result
    
    return result


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract refusal rates by attack type with Q type breakdowns")
    parser.add_argument(
        "--input",
        type=str,
        default="prevention_refusal_rates_consolidated.json",
        help="Input consolidated JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="refusal_rates_with_qtype.json",
        help="Output JSON file"
    )
    
    args = parser.parse_args()
    
    # Load consolidated data
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract breakdowns for each model
    result = {
        'metadata': {
            'description': 'Refusal rates by attack type with question type breakdowns',
            'confidence_level': 0.95,
            'models': list(data['breakdown'].keys())
        },
        'by_model': {}
    }
    
    for model_name, breakdown_data in data['breakdown'].items():
        by_attack_qtype = aggregate_by_attack_and_qtype(breakdown_data)
        result['by_model'][model_name] = by_attack_qtype
    
    # Save output
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("="*100)
    print("REFUSAL RATES BY ATTACK TYPE WITH QUESTION TYPE BREAKDOWNS")
    print("="*100)
    print()
    
    # Define attack type order
    attack_order = [
        'icw',
        'dual_layer_gibberish',
        'dual_layer_refusal_string',
        'font_attack_gibberish',
        'font_attack_refusal_string',
        'icw_dual_layer_gibberish',
        'icw_dual_layer_refusal_string',
        'icw_font_attack_gibberish',
        'icw_font_attack_refusal_string'
    ]
    
    qtype_order = ['MCQ', 'LONG', 'TF']
    
    for model_name in sorted(result['by_model'].keys()):
        model_data = result['by_model'][model_name]
        print(f"\n{model_name.upper()}")
        print("-" * 100)
        
        for attack_type in attack_order:
            if attack_type not in model_data:
                continue
            
            attack_data = model_data[attack_type]
            print(f"\n  {attack_type}:")
            
            # Overall stats (sum across all qtypes)
            total_refused = sum(d['refused_count'] for d in attack_data.values())
            total_questions = sum(d['total_questions'] for d in attack_data.values())
            overall_rate = (total_refused / total_questions * 100) if total_questions > 0 else 0.0
            ci_lower, ci_upper = wilson_confidence_interval(total_refused, total_questions, 0.95)
            
            print(f"    Overall: {overall_rate:.2f}% [{ci_lower*100:.2f}%, {ci_upper*100:.2f}%] (n={total_questions})")
            
            # By question type
            for qtype in qtype_order:
                if qtype in attack_data:
                    stats = attack_data[qtype]
                    print(f"      {qtype}: {stats['refusal_rate']:.2f}% "
                          f"[{stats['confidence_interval_95']['lower']:.2f}%, "
                          f"{stats['confidence_interval_95']['upper']:.2f}%] "
                          f"(n={stats['total_questions']})")
    
    print("\n" + "="*100)
    print(f"✓ Results saved to {output_path}")
    print("="*100)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
