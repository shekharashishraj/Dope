#!/usr/bin/env python3
"""Extract simple refusal rates and confidence intervals for all 9 attack types per model."""
import json
import sys
from pathlib import Path


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract simple refusal rates by attack type")
    parser.add_argument(
        "--input",
        type=str,
        default="model_wise_refusal_rates.json",
        help="Input JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="simple_refusal_rates.json",
        help="Output JSON file"
    )
    
    args = parser.parse_args()
    
    # Load data
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract simplified data
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
    
    for model_name in sorted(data['by_model'].keys()):
        model_data = data['by_model'][model_name]
        attack_data = model_data['by_attack_type']
        
        result[model_name] = {}
        for attack_type in attack_order:
            if attack_type in attack_data:
                stats = attack_data[attack_type]
                result[model_name][attack_type] = {
                    'refusal_rate': stats['refusal_rate'],
                    'confidence_interval_95': {
                        'lower': stats['confidence_interval_95']['lower'],
                        'upper': stats['confidence_interval_95']['upper']
                    }
                }
    
    # Save output
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print table
    print("="*100)
    print("REFUSAL RATES BY ATTACK TYPE (9 ATTACK TYPES)")
    print("="*100)
    print()
    
    # Header
    print(f"{'Attack Type':<35}", end="")
    for model_name in sorted(result.keys()):
        print(f"{model_name:>20}", end="")
    print()
    print("-" * 100)
    
    # Data rows
    for attack_type in attack_order:
        print(f"{attack_type:<35}", end="")
        for model_name in sorted(result.keys()):
            if attack_type in result[model_name]:
                stats = result[model_name][attack_type]
                rate = stats['refusal_rate']
                ci_lower = stats['confidence_interval_95']['lower']
                ci_upper = stats['confidence_interval_95']['upper']
                print(f"{rate:>6.2f}% [{ci_lower:>5.2f}, {ci_upper:>5.2f}]", end="")
            else:
                print(f"{'N/A':>20}", end="")
        print()
    
    print()
    print("="*100)
    print(f"✓ Results saved to {output_path}")
    print("="*100)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
