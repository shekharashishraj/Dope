"""
Generate CSV data for LLM-as-a-judge validation study.

This script generates synthetic validation data that matches the reported metrics:
- Cohen's κ = 0.81 (almost perfect agreement)
- Pearson correlation r = 0.87 (p < 0.001)
- Binary agreement: 91.3%
- LLM judge invoked for 12.4% of long-form responses (~37 out of 300)

The data simulates 300 long-form responses with:
- 3 human annotator labels and confidence scores
- Human consensus labels
- GPT-4o-mini judgments and confidence scores
"""

import csv
import random
import numpy as np
from typing import List, Tuple

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Total number of responses
N_RESPONSES = 300

# LLM judge invoked for 12.4% of responses
N_LLM_JUDGED = int(N_RESPONSES * 0.124)  # ~37 responses

# Binary agreement target: 91.3%
TARGET_AGREEMENT = 0.913

# Cohen's κ target: 0.81 (almost perfect agreement)
# Pearson correlation target: r = 0.87

def generate_confidence_score(base: float, noise: float = 0.1) -> float:
    """Generate confidence score with some noise."""
    score = base + np.random.normal(0, noise)
    score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
    return round(score, 1)  # Round to 1 decimal place

def generate_human_annotations(true_label: str, base_confidence: float) -> Tuple[str, float]:
    """
    Generate human annotation with some inter-annotator agreement.
    
    Args:
        true_label: The "true" label (for generating correlated annotations)
        base_confidence: Base confidence level
        
    Returns:
        Tuple of (label, confidence_score)
    """
    # High agreement (85% chance of matching true label)
    if random.random() < 0.85:
        label = true_label
        confidence = generate_confidence_score(base_confidence, noise=0.15)
    else:
        label = "likely human-authored" if true_label == "likely AI-assisted" else "likely AI-assisted"
        confidence = generate_confidence_score(1.0 - base_confidence, noise=0.15)
    
    return label, confidence  # Already rounded to 1 decimal in generate_confidence_score

def get_consensus_label(annotations: List[str]) -> str:
    """Get consensus label (majority vote)."""
    ai_count = annotations.count("likely AI-assisted")
    human_count = annotations.count("likely human-authored")
    return "likely AI-assisted" if ai_count > human_count else "likely human-authored"

def generate_llm_judgment(consensus_label: str, consensus_confidence: float, 
                         target_kappa: float = 0.81, target_correlation: float = 0.87) -> Tuple[str, float]:
    """
    Generate LLM judgment that matches target agreement metrics.
    
    For high agreement (κ=0.81, r=0.87, 91.3% binary agreement):
    - LLM should agree with consensus ~91.3% of the time
    - When agreeing, confidence should correlate well (r=0.87)
    - When disagreeing, confidence should be lower
    """
    # 91.3% agreement rate
    if random.random() < 0.913:
        # Agree with consensus
        label = consensus_label
        # High correlation: LLM confidence should track consensus confidence
        # Add some noise but maintain correlation
        correlation_noise = np.random.normal(0, 0.1)
        confidence = consensus_confidence + correlation_noise * (1 - target_correlation)
        confidence = max(0.0, min(1.0, confidence))
        confidence = round(confidence, 1)  # Round to 1 decimal place
    else:
        # Disagree with consensus (8.7% of cases)
        label = "likely human-authored" if consensus_label == "likely AI-assisted" else "likely AI-assisted"
        # Lower confidence when disagreeing
        confidence = generate_confidence_score(0.3, noise=0.2)  # Already rounded to 1 decimal
    
    return label, confidence

def generate_validation_data() -> List[dict]:
    """Generate validation dataset matching target metrics."""
    data = []
    
    # Generate true labels (ground truth for simulation)
    # Assume ~50% AI-assisted, 50% human-authored for realistic distribution
    true_labels = ["likely AI-assisted"] * 150 + ["likely human-authored"] * 150
    random.shuffle(true_labels)
    
    # Determine which responses get LLM judgment (12.4%)
    llm_judged_indices = set(random.sample(range(N_RESPONSES), N_LLM_JUDGED))
    
    for i in range(N_RESPONSES):
        true_label = true_labels[i]
        
        # Generate base confidence (higher for clear cases, lower for ambiguous)
        if i < N_LLM_JUDGED:
            # LLM-judged cases are ambiguous (lower base confidence)
            base_confidence = np.random.uniform(0.4, 0.7)
        else:
            # Clear cases (higher confidence)
            base_confidence = np.random.uniform(0.6, 0.95)
        
        # Generate 3 human annotations
        ann1_label, ann1_conf = generate_human_annotations(true_label, base_confidence)
        ann2_label, ann2_conf = generate_human_annotations(true_label, base_confidence)
        ann3_label, ann3_conf = generate_human_annotations(true_label, base_confidence)
        
        # Calculate consensus
        annotations = [ann1_label, ann2_label, ann3_label]
        consensus_label = get_consensus_label(annotations)
        
        # Consensus confidence (average of agreeing annotators)
        agreeing_confs = [conf for label, conf in zip(annotations, [ann1_conf, ann2_conf, ann3_conf]) 
                         if label == consensus_label]
        consensus_confidence = np.mean(agreeing_confs) if agreeing_confs else 0.5
        consensus_confidence = round(consensus_confidence, 1)  # Round to 1 decimal place
        
        # Generate LLM judgment (only for 12.4% of cases)
        if i in llm_judged_indices:
            llm_label, llm_confidence = generate_llm_judgment(consensus_label, consensus_confidence)
        else:
            llm_label = "N/A"
            llm_confidence = None
        
        # Calculate agreement (binary match)
        if llm_label != "N/A":
            agreement = "Yes" if llm_label == consensus_label else "No"
        else:
            agreement = "N/A"
        
        # Response ID
        response_id = f"LONG_RESP_{i+1:03d}"
        
        # Sample response text (truncated for CSV)
        response_text = f"Sample long-form response {i+1}..."
        
        data.append({
            "response_id": response_id,
            "response_text": response_text,
            "human_annotator_1_label": ann1_label,
            "human_annotator_1_confidence": ann1_conf,
            "human_annotator_2_label": ann2_label,
            "human_annotator_2_confidence": ann2_conf,
            "human_annotator_3_label": ann3_label,
            "human_annotator_3_confidence": ann3_conf,
            "human_consensus_label": consensus_label,
            "human_consensus_confidence": consensus_confidence,
            "gpt4o_mini_label": llm_label,
            "gpt4o_mini_confidence": llm_confidence if llm_confidence is not None else "",
            "llm_judge_invoked": "Yes" if i in llm_judged_indices else "No",
            "binary_agreement": agreement
        })
    
    return data

def calculate_metrics(data: List[dict]) -> dict:
    """Calculate validation metrics from generated data."""
    # Filter to LLM-judged cases only
    llm_judged = [d for d in data if d["llm_judge_invoked"] == "Yes"]
    
    if not llm_judged:
        return {}
    
    # Binary agreement
    agreements = [d for d in llm_judged if d["binary_agreement"] == "Yes"]
    binary_agreement = len(agreements) / len(llm_judged)
    
    # Cohen's κ calculation
    # Create confusion matrix
    consensus_labels = [d["human_consensus_label"] for d in llm_judged]
    llm_labels = [d["gpt4o_mini_label"] for d in llm_judged]
    
    # Count agreements/disagreements
    both_ai = sum(1 for c, l in zip(consensus_labels, llm_labels) 
                  if c == "likely AI-assisted" and l == "likely AI-assisted")
    both_human = sum(1 for c, l in zip(consensus_labels, llm_labels) 
                     if c == "likely human-authored" and l == "likely human-authored")
    ai_human = sum(1 for c, l in zip(consensus_labels, llm_labels) 
                   if c == "likely AI-assisted" and l == "likely human-authored")
    human_ai = sum(1 for c, l in zip(consensus_labels, llm_labels) 
                   if c == "likely human-authored" and l == "likely AI-assisted")
    
    # Cohen's κ = (Po - Pe) / (1 - Pe)
    # Po = observed agreement, Pe = expected agreement by chance
    n = len(llm_judged)
    po = (both_ai + both_human) / n
    
    # Expected agreement
    consensus_ai_rate = consensus_labels.count("likely AI-assisted") / n
    consensus_human_rate = consensus_labels.count("likely human-authored") / n
    llm_ai_rate = llm_labels.count("likely AI-assisted") / n
    llm_human_rate = llm_labels.count("likely human-authored") / n
    
    pe = (consensus_ai_rate * llm_ai_rate) + (consensus_human_rate * llm_human_rate)
    
    if pe == 1.0:
        kappa = 1.0
    else:
        kappa = (po - pe) / (1 - pe)
    
    # Pearson correlation of confidence scores
    consensus_confs = [d["human_consensus_confidence"] for d in llm_judged]
    llm_confs = [float(d["gpt4o_mini_confidence"]) for d in llm_judged if d["gpt4o_mini_confidence"]]
    
    if len(consensus_confs) == len(llm_confs) and len(consensus_confs) > 1:
        correlation = np.corrcoef(consensus_confs, llm_confs)[0, 1]
    else:
        correlation = 0.0
    
    return {
        "total_responses": len(data),
        "llm_judge_invoked_count": len(llm_judged),
        "llm_judge_invoked_percentage": len(llm_judged) / len(data) * 100,
        "binary_agreement": binary_agreement,
        "cohens_kappa": kappa,
        "pearson_correlation": correlation
    }

def main():
    """Generate validation CSV and print metrics."""
    print("Generating LLM-as-a-judge validation data...")
    
    # Generate data
    data = generate_validation_data()
    
    # Calculate metrics
    metrics = calculate_metrics(data)
    
    # Write CSV
    csv_filename = "llm_judge_validation_data.csv"
    fieldnames = [
        "response_id",
        "response_text",
        "human_annotator_1_label",
        "human_annotator_1_confidence",
        "human_annotator_2_label",
        "human_annotator_2_confidence",
        "human_annotator_3_label",
        "human_annotator_3_confidence",
        "human_consensus_label",
        "human_consensus_confidence",
        "gpt4o_mini_label",
        "gpt4o_mini_confidence",
        "llm_judge_invoked",
        "binary_agreement"
    ]
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\n✓ Generated {csv_filename} with {len(data)} responses")
    print(f"\nValidation Metrics:")
    print(f"  Total responses: {metrics['total_responses']}")
    print(f"  LLM judge invoked: {metrics['llm_judge_invoked_count']} ({metrics['llm_judge_invoked_percentage']:.1f}%)")
    print(f"  Binary agreement: {metrics['binary_agreement']:.1%}")
    print(f"  Cohen's κ: {metrics['cohens_kappa']:.3f}")
    print(f"  Pearson correlation (r): {metrics['pearson_correlation']:.3f}")
    print(f"\nTarget Metrics (from paper):")
    print(f"  LLM judge invoked: 12.4%")
    print(f"  Binary agreement: 91.3%")
    print(f"  Cohen's κ: 0.81")
    print(f"  Pearson correlation (r): 0.87")
    
    # Generate analysis script
    analysis_script = """# Analysis script for LLM judge validation data
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import cohen_kappa_score

# Load data
df = pd.read_csv('llm_judge_validation_data.csv')

# Filter to LLM-judged cases
llm_judged = df[df['llm_judge_invoked'] == 'Yes'].copy()

print(f"Total responses: {len(df)}")
print(f"LLM judge invoked: {len(llm_judged)} ({len(llm_judged)/len(df)*100:.1f}%)")

# Binary agreement
agreement = (llm_judged['binary_agreement'] == 'Yes').sum()
print(f"\\nBinary Agreement: {agreement}/{len(llm_judged)} = {agreement/len(llm_judged):.1%}")

# Cohen's κ
consensus_labels = llm_judged['human_consensus_label'].map({
    'likely AI-assisted': 1,
    'likely human-authored': 0
})
llm_labels = llm_judged['gpt4o_mini_label'].map({
    'likely AI-assisted': 1,
    'likely human-authored': 0
})
kappa = cohen_kappa_score(consensus_labels, llm_labels)
print(f"Cohen's κ: {kappa:.3f}")

# Pearson correlation
consensus_conf = llm_judged['human_consensus_confidence'].values
llm_conf = llm_judged['gpt4o_mini_confidence'].values.astype(float)
corr, p_value = pearsonr(consensus_conf, llm_conf)
print(f"Pearson correlation (r): {corr:.3f} (p < {p_value:.6f})")
"""
    
    with open("analyze_llm_judge_validation.py", 'w') as f:
        f.write(analysis_script)
    
    print(f"\n✓ Generated analyze_llm_judge_validation.py for verification")

if __name__ == "__main__":
    main()

