# Analysis script for LLM judge validation data
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
print(f"\nBinary Agreement: {agreement}/{len(llm_judged)} = {agreement/len(llm_judged):.1%}")

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
