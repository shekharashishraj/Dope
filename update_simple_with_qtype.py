#!/usr/bin/env python3
"""Update simple_refusal_rates.json to include question type breakdowns."""
import json
import sys
from pathlib import Path


def main():
    """Main entry point."""
    # Load the data with question types
    with open('refusal_rates_with_qtype.json', 'r', encoding='utf-8') as f:
        qtype_data = json.load(f)
    
    # Create simplified structure
    result = {}
    
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
    
    for model_name in sorted(qtype_data['by_model'].keys()):
        model_data = qtype_data['by_model'][model_name]
        result[model_name] = {}
        
        for attack_type in attack_order:
            if attack_type not in model_data:
                continue
            
            attack_data = model_data[attack_type]
            
            # Calculate overall
            total_refused = sum(d['refused_count'] for d in attack_data.values())
            total_questions = sum(d['total_questions'] for d in attack_data.values())
            overall_rate = (total_refused / total_questions * 100) if total_questions > 0 else 0.0
            
            # Get overall CI from first entry (or calculate)
            from math import sqrt
            z = 1.96
            p = total_refused / total_questions if total_questions > 0 else 0.0
            n = total_questions
            
            denominator = 1 + (z**2 / n) if n > 0 else 1
            center = (p + (z**2 / (2 * n))) / denominator if n > 0 else 0.0
            margin = (z / denominator) * sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2))) if n > 0 else 0.0
            
            ci_lower = max(0.0, (center - margin) * 100)
            ci_upper = min(100.0, (center + margin) * 100)
            
            result[model_name][attack_type] = {
                'refusal_rate': round(overall_rate, 2),
                'confidence_interval_95': {
                    'lower': round(ci_lower, 2),
                    'upper': round(ci_upper, 2)
                },
                'by_question_type': {}
            }
            
            # Add question type breakdowns
            for qtype in qtype_order:
                if qtype in attack_data:
                    stats = attack_data[qtype]
                    result[model_name][attack_type]['by_question_type'][qtype] = {
                        'refusal_rate': stats['refusal_rate'],
                        'confidence_interval_95': {
                            'lower': stats['confidence_interval_95']['lower'],
                            'upper': stats['confidence_interval_95']['upper']
                        }
                    }
    
    # Save updated file
    output_path = Path('simple_refusal_rates.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("="*100)
    print("UPDATED: REFUSAL RATES BY ATTACK TYPE WITH QUESTION TYPE BREAKDOWNS")
    print("="*100)
    print()
    
    for model_name in sorted(result.keys()):
        model_data = result[model_name]
        print(f"\n{model_name.upper()}")
        print("-" * 100)
        
        for attack_type in attack_order:
            if attack_type not in model_data:
                continue
            
            attack_stats = model_data[attack_type]
            print(f"\n  {attack_type}:")
            print(f"    Overall: {attack_stats['refusal_rate']:.2f}% "
                  f"[{attack_stats['confidence_interval_95']['lower']:.2f}%, "
                  f"{attack_stats['confidence_interval_95']['upper']:.2f}%]")
            
            for qtype in qtype_order:
                if qtype in attack_stats['by_question_type']:
                    qtype_stats = attack_stats['by_question_type'][qtype]
                    print(f"      {qtype}: {qtype_stats['refusal_rate']:.2f}% "
                          f"[{qtype_stats['confidence_interval_95']['lower']:.2f}%, "
                          f"{qtype_stats['confidence_interval_95']['upper']:.2f}%]")
    
    print("\n" + "="*100)
    print(f"✓ Updated simple_refusal_rates.json with question type breakdowns")
    print("="*100)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
