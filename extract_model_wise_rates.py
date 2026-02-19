#!/usr/bin/env python3
"""Extract model-wise refusal rates by question type and attack type from consolidated data."""
import json
import sys
from pathlib import Path
from collections import defaultdict


def aggregate_by_question_type(breakdown_data: dict) -> dict:
    """Aggregate refusal rates by question type across all domains and attack types."""
    by_qtype = defaultdict(lambda: {'refused': 0, 'total': 0})
    
    for domain_data in breakdown_data.values():
        for qtype, type_data in domain_data.items():
            for method_data in type_data.values():
                for variant_data in method_data.values():
                    by_qtype[qtype]['refused'] += variant_data['refused_count']
                    by_qtype[qtype]['total'] += variant_data['total_questions']
    
    # Calculate rates and CIs
    result = {}
    for qtype, counts in by_qtype.items():
        if counts['total'] == 0:
            continue
        
        refusal_rate = (counts['refused'] / counts['total']) * 100
        # Use Wilson CI (approximate for large samples)
        from math import sqrt
        z = 1.96
        p = counts['refused'] / counts['total']
        n = counts['total']
        
        denominator = 1 + (z**2 / n)
        center = (p + (z**2 / (2 * n))) / denominator
        margin = (z / denominator) * sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2)))
        
        ci_lower = max(0.0, (center - margin) * 100)
        ci_upper = min(100.0, (center + margin) * 100)
        
        result[qtype] = {
            'total_questions': counts['total'],
            'refused_count': counts['refused'],
            'answered_count': counts['total'] - counts['refused'],
            'refusal_rate': round(refusal_rate, 2),
            'confidence_interval_95': {
                'lower': round(ci_lower, 2),
                'upper': round(ci_upper, 2)
            }
        }
    
    return result


def aggregate_by_attack_type(breakdown_data: dict) -> dict:
    """Aggregate refusal rates by attack type (method+variant) across all domains and question types."""
    by_attack = defaultdict(lambda: {'refused': 0, 'total': 0})
    
    for domain_data in breakdown_data.values():
        for type_data in domain_data.values():
            for method, method_data in type_data.items():
                for variant, variant_data in method_data.items():
                    # Create attack type key: method_variant or just method for ICW
                    if method == 'icw':
                        attack_key = 'icw'
                    else:
                        attack_key = f"{method}_{variant}"
                    
                    by_attack[attack_key]['refused'] += variant_data['refused_count']
                    by_attack[attack_key]['total'] += variant_data['total_questions']
    
    # Calculate rates and CIs
    result = {}
    for attack_type, counts in sorted(by_attack.items()):
        if counts['total'] == 0:
            continue
        
        refusal_rate = (counts['refused'] / counts['total']) * 100
        # Use Wilson CI
        from math import sqrt
        z = 1.96
        p = counts['refused'] / counts['total']
        n = counts['total']
        
        denominator = 1 + (z**2 / n)
        center = (p + (z**2 / (2 * n))) / denominator
        margin = (z / denominator) * sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2)))
        
        ci_lower = max(0.0, (center - margin) * 100)
        ci_upper = min(100.0, (center + margin) * 100)
        
        result[attack_type] = {
            'total_questions': counts['total'],
            'refused_count': counts['refused'],
            'answered_count': counts['total'] - counts['refused'],
            'refusal_rate': round(refusal_rate, 2),
            'confidence_interval_95': {
                'lower': round(ci_lower, 2),
                'upper': round(ci_upper, 2)
            }
        }
    
    return result


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract model-wise refusal rates by Q type and attack type")
    parser.add_argument(
        "--input",
        type=str,
        default="prevention_refusal_rates_consolidated.json",
        help="Input consolidated JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="model_wise_refusal_rates.json",
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
            'description': 'Model-wise refusal rates by question type and attack type',
            'confidence_level': 0.95,
            'models': list(data['breakdown'].keys())
        },
        'by_model': {}
    }
    
    for model_name, breakdown_data in data['breakdown'].items():
        by_qtype = aggregate_by_question_type(breakdown_data)
        by_attack = aggregate_by_attack_type(breakdown_data)
        
        result['by_model'][model_name] = {
            'by_question_type': by_qtype,
            'by_attack_type': by_attack
        }
    
    # Save output
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("="*80)
    print("MODEL-WISE REFUSAL RATES")
    print("="*80)
    
    for model_name in sorted(result['by_model'].keys()):
        model_data = result['by_model'][model_name]
        print(f"\n{model_name.upper()}")
        print("-" * 80)
        
        print("\n📊 BY QUESTION TYPE:")
        for qtype in sorted(model_data['by_question_type'].keys()):
            stats = model_data['by_question_type'][qtype]
            print(f"  {qtype}:")
            print(f"    Refusal Rate: {stats['refusal_rate']:.2f}%")
            print(f"    95% CI: [{stats['confidence_interval_95']['lower']:.2f}%, {stats['confidence_interval_95']['upper']:.2f}%]")
            print(f"    Total: {stats['total_questions']:,} (Refused: {stats['refused_count']:,}, Answered: {stats['answered_count']:,})")
        
        print("\n🎯 BY ATTACK TYPE:")
        # Order: icw, then others alphabetically
        attack_order = ['icw'] + [k for k in sorted(model_data['by_attack_type'].keys()) if k != 'icw']
        for attack_type in attack_order:
            if attack_type not in model_data['by_attack_type']:
                continue
            stats = model_data['by_attack_type'][attack_type]
            print(f"  {attack_type}:")
            print(f"    Refusal Rate: {stats['refusal_rate']:.2f}%")
            print(f"    95% CI: [{stats['confidence_interval_95']['lower']:.2f}%, {stats['confidence_interval_95']['upper']:.2f}%]")
            print(f"    Total: {stats['total_questions']:,} (Refused: {stats['refused_count']:,}, Answered: {stats['answered_count']:,})")
    
    print("\n" + "="*80)
    print(f"✓ Results saved to {output_path}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
