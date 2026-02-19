#!/usr/bin/env python3
"""Generate fake refusal rates following the trend: icw_font > icw_dual_layer > font > dual_layer > icw."""
import json
import random
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


def generate_refusal_rate(base_rate: float, variance: float = 0.02) -> float:
    """Generate a refusal rate with small variance around base rate."""
    # Add small random variation (±variance)
    variation = random.uniform(-variance, variance)
    rate = base_rate + variation
    # Clamp to [60, 100] to ensure all values are in the requested range
    # But allow more natural distribution - only clamp if way out of range
    if rate < 60.0:
        # For values that would be below 60, add some variation to distribute them in 60-70 range
        rate = 60.0 + random.uniform(0, 10.0)
    return min(100.0, rate)


def create_fake_stats(refusal_rate: float, n: int) -> dict:
    """Create fake statistics for a given refusal rate and sample size."""
    # Ensure rate is at least 60% but allow natural distribution
    if refusal_rate < 60.0:
        # Distribute in 60-70 range instead of clamping to exactly 60
        refusal_rate = 60.0 + random.uniform(0, 10.0)
    
    refused_count = int(round(n * refusal_rate / 100))
    answered_count = n - refused_count
    
    # Recalculate actual rate from counts
    actual_rate = (refused_count / n * 100) if n > 0 else 0.0
    # Ensure final rate is at least 60% but allow natural distribution
    if actual_rate < 60.0:
        actual_rate = 60.0 + random.uniform(0, 10.0)
    
    ci_lower, ci_upper = wilson_confidence_interval(refused_count, n, 0.95)
    
    return {
        'refusal_rate': round(actual_rate, 2),
        'confidence_interval_95': {
            'lower': round(ci_lower * 100, 2),
            'upper': round(ci_upper * 100, 2)
        }
    }


def main():
    """Main entry point."""
    # Define the trend: icw_font (high 90s) > icw_dual_layer > font (80s) > dual_layer (80s) > icw (60s-70s)
    # Base rates for each attack type - all between 60-100%
    base_rates = {
        'icw_font_attack_gibberish': 97.5,  # High 90s
        'icw_font_attack_refusal_string': 98.5,  # High 90s
        'icw_dual_layer_gibberish': 94.0,  # Next highest
        'icw_dual_layer_refusal_string': 95.0,  # Next highest
        'font_attack_gibberish': 83.0,  # 80s range (raised to ensure 80s even after adjustments)
        'font_attack_refusal_string': 86.0,  # 80s range (refusal string works better)
        'dual_layer_gibberish': 83.0,  # 80s range (raised to ensure 80s even after adjustments)
        'dual_layer_refusal_string': 88.0,  # 80s range (refusal string works better)
        'icw': 65.0  # 60s-70s range (will be distributed with variation)
    }
    
    # Model-specific adjustments (to maintain some variation while keeping trend)
    # Adjusted to ensure font_attack and dual_layer stay in 80s for all models
    model_adjustments = {
        'gpt-5.1': {'offset': 0.0, 'multiplier': 1.0},  # Highest performing - keep high 90s
        'gpt-4o': {'offset': -2.0, 'multiplier': 0.99},  # Slightly lower but still high
        'claude-sonnet-4-5': {'offset': -2.0, 'multiplier': 0.98},  # Lower but font/dual still in 80s
        'claude-opus-4-5': {'offset': -3.0, 'multiplier': 0.97}  # Lowest but font/dual still in 80s
    }
    
    # Sample sizes (approximate, based on real data)
    sample_sizes = {
        'MCQ': 683,  # For full runs
        'LONG': 247,
        'TF': 767
    }
    
    # Limited run sample sizes (for Claude models)
    limited_sample_sizes = {
        'MCQ': 155,
        'LONG': 50,
        'TF': 215
    }
    
    result = {}
    
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
    
    for model_name in ['gpt-5.1', 'gpt-4o', 'claude-sonnet-4-5', 'claude-opus-4-5']:
        result[model_name] = {}
        adjustment = model_adjustments[model_name]
        
        # Determine if limited or full run
        is_limited = 'claude' in model_name
        sizes = limited_sample_sizes if is_limited else sample_sizes
        
        for attack_type in attack_order:
            # Get base rate for this attack type
            base_rate = base_rates.get(attack_type, 50.0)
            
            # Apply model adjustment
            adjusted_base = base_rate * adjustment['multiplier'] + adjustment['offset']
            # Ensure all values are between 60-100%
            adjusted_base = max(60.0, min(100.0, adjusted_base))
            
            # Generate overall stats with model-specific variation
            overall_n = sum(sizes.values())
            # Add more variance between models (±3-5%)
            model_variance = random.uniform(-4.0, 4.0)
            overall_base = max(60.0, min(100.0, adjusted_base + model_variance))
            overall_rate = generate_refusal_rate(overall_base, variance=0.02)
            overall_stats = create_fake_stats(overall_rate, overall_n)
            
            result[model_name][attack_type] = {
                'refusal_rate': overall_stats['refusal_rate'],
                'confidence_interval_95': overall_stats['confidence_interval_95'],
                'by_question_type': {}
            }
            
            # Generate question type breakdowns with more variation
            for qtype in qtype_order:
                n = sizes[qtype]
                # Add significant variation per question type (±4-6%)
                # Different question types should have different rates
                if attack_type == 'icw':
                    # ICW: more variation in 60s-70s
                    qtype_variance = random.uniform(-6.0, 6.0)
                else:
                    # Other attacks: variation based on question type
                    if qtype == 'MCQ':
                        qtype_variance = random.uniform(-4.0, 4.0)
                    elif qtype == 'LONG':
                        qtype_variance = random.uniform(-5.0, 5.0)
                    else:  # TF
                        qtype_variance = random.uniform(-4.0, 4.0)
                
                qtype_base = max(60.0, min(100.0, adjusted_base + model_variance + qtype_variance))
                qtype_rate = generate_refusal_rate(qtype_base, variance=0.02)
                qtype_stats = create_fake_stats(qtype_rate, n)
                
                result[model_name][attack_type]['by_question_type'][qtype] = {
                    'refusal_rate': qtype_stats['refusal_rate'],
                    'confidence_interval_95': qtype_stats['confidence_interval_95']
                }
    
    # Save to file
    output_path = 'simple_refusal_rates_fake.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("="*100)
    print("GENERATED FAKE REFUSAL RATES (Following Trend: icw_font > icw_dual_layer > font > dual_layer > icw)")
    print("="*100)
    print()
    
    for model_name in sorted(result.keys()):
        print(f"\n{model_name.upper()}")
        print("-" * 100)
        
        for attack_type in attack_order:
            if attack_type in result[model_name]:
                stats = result[model_name][attack_type]
                print(f"\n  {attack_type}:")
                print(f"    Overall: {stats['refusal_rate']:.2f}% "
                      f"[{stats['confidence_interval_95']['lower']:.2f}%, "
                      f"{stats['confidence_interval_95']['upper']:.2f}%]")
                
                for qtype in qtype_order:
                    if qtype in stats['by_question_type']:
                        qtype_stats = stats['by_question_type'][qtype]
                        print(f"      {qtype}: {qtype_stats['refusal_rate']:.2f}% "
                              f"[{qtype_stats['confidence_interval_95']['lower']:.2f}%, "
                              f"{qtype_stats['confidence_interval_95']['upper']:.2f}%]")
    
    print("\n" + "="*100)
    print(f"✓ Fake data saved to {output_path}")
    print("="*100)
    
    # Verify trend
    print("\n\nTREND VERIFICATION (Overall rates):")
    print("="*100)
    for model_name in sorted(result.keys()):
        print(f"\n{model_name}:")
        rates = []
        for attack_type in attack_order:
            if attack_type in result[model_name]:
                rate = result[model_name][attack_type]['refusal_rate']
                rates.append((attack_type, rate))
        
        # Sort by rate (descending)
        rates.sort(key=lambda x: x[1], reverse=True)
        for i, (attack, rate) in enumerate(rates, 1):
            print(f"  {i}. {attack:35s}: {rate:6.2f}%")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
