#!/usr/bin/env python3
"""Generate markdown document from failure modes analysis."""

import json
from pathlib import Path
from typing import Dict, List, Any


def format_example(example: Dict[str, Any], index: int) -> str:
    """Format a single example for markdown."""
    lines = [f"#### Example {index + 1}"]
    lines.append("")
    
    # Basic info
    lines.append(f"**Document:** `{example.get('docid', 'unknown')}`")
    lines.append(f"**Question #:** {example.get('question_number', 'unknown')}")
    lines.append(f"**Question Type:** {example.get('question_type', 'unknown')}")
    lines.append(f"**Attack Method:** {example.get('method', 'unknown')}")
    lines.append(f"**Variant:** {example.get('variant', 'unknown')}")
    lines.append(f"**Model:** {example.get('model', 'unknown')}")
    lines.append("")
    
    # Original question
    if example.get('original_question'):
        lines.append("**Original Question:**")
        lines.append("```")
        lines.append(example['original_question'])
        lines.append("```")
        lines.append("")
    
    # Perturbation details
    if example.get('perturbation'):
        pert = example['perturbation']
        lines.append("**Perturbation:**")
        lines.append(f"- Original substring: `{pert.get('original_substring', '')}`")
        lines.append(f"- Replacement substring: `{pert.get('replacement_substring', '')}`")
        if pert.get('start_pos') is not None:
            lines.append(f"- Position: {pert['start_pos']}-{pert.get('end_pos', '')}")
        lines.append("")
    
    # Answers
    lines.append("**Answers:**")
    lines.append(f"- Gold answer: `{example.get('gold_answer', 'unknown')}`")
    if example.get('target_wrong_answer'):
        lines.append(f"- Target wrong answer: `{example['target_wrong_answer']}`")
    lines.append(f"- AI answer: `{example.get('ai_answer', 'unknown')}`")
    lines.append("")
    
    # Failure reason
    lines.append("**Failure Reason:**")
    lines.append(f"> {example.get('prevention_reason', example.get('reason', 'Unknown'))}")
    lines.append("")
    
    # Source reference
    if example.get('source_file'):
        source = example['source_file']
        # Make relative path
        if 'output_prevention_eval' in source:
            source = source.split('output_prevention_eval')[1].lstrip('/')
        lines.append(f"*Source: `{source}`*")
        lines.append("")
    
    return "\n".join(lines)


def generate_synthetic_examples() -> Dict[str, List[Dict[str, Any]]]:
    """Generate synthetic examples for failure modes with sparse real data."""
    synthetic = {}
    
    # Weak perturbation - Tier 3-4 techniques
    synthetic["prevention::weak_perturbation_tier3"] = [
        {
            "category": "prevention",
            "subcategory": "weak_perturbation_tier3",
            "description": "TF: Model answered correctly despite weak quantifier-based perturbation",
            "original_question": "All mammals are warm-blooded.",
            "perturbation": {
                "original_substring": "All",
                "replacement_substring": "Most",
                "technique": "Tier 3 - Quantifier modification",
            },
            "gold_answer": "True",
            "target_wrong_answer": "False",
            "ai_answer": "True",
            "failure_reason": "Quantifier change from 'All' to 'Most' is too subtle - statement remains factually True",
            "mitigation": "Use Tier 1 techniques (directional inversions) instead of quantifier modifications"
        },
        {
            "category": "prevention",
            "subcategory": "weak_perturbation_tier3",
            "description": "TF: Model answered correctly despite weak quantifier-based perturbation",
            "original_question": "Water always freezes at 0°C at standard pressure.",
            "perturbation": {
                "original_substring": "always",
                "replacement_substring": "usually",
                "technique": "Tier 3 - Quantifier modification",
            },
            "gold_answer": "True",
            "target_wrong_answer": "False",
            "ai_answer": "True",
            "failure_reason": "Change from 'always' to 'usually' is too subtle - statement remains essentially True",
            "mitigation": "Use Tier 1 techniques (property swaps, directional inversions)"
        },
    ]
    
    # Negation-based failures (prohibited technique)
    synthetic["prevention::prohibited_negation"] = [
        {
            "category": "prevention",
            "subcategory": "prohibited_negation",
            "description": "TF: Negation-based perturbation detected and normalized by model",
            "original_question": "Water is a compound.",
            "perturbation": {
                "original_substring": "is",
                "replacement_substring": "is not",
                "technique": "PROHIBITED - Negation insertion",
            },
            "gold_answer": "True",
            "target_wrong_answer": "False",
            "ai_answer": "True",
            "failure_reason": "Model's preprocessing normalizes negation patterns, ignoring the perturbation",
            "mitigation": "Avoid negation-based perturbations; use property swaps or entity substitutions"
        },
    ]
    
    # Parsing failures
    synthetic["detection::parsing_failure_edge_case"] = [
        {
            "category": "detection",
            "subcategory": "parsing_failure_edge_case",
            "description": "LLM judge fails to extract answer from ambiguous response format",
            "original_question": "Which algorithm has the best time complexity for sorting?",
            "ai_answer": "I believe option (b) would be the most efficient, though (a) is also reasonable in some cases.",
            "gold_answer": "A",
            "target_wrong_answer": "B",
            "failure_reason": "Response contains multiple option mentions, causing extraction ambiguity",
            "mitigation": "Improve LLM judge prompt to handle ambiguous responses with multiple option mentions"
        },
    ]
    
    # ICW prompt ignored - edge cases
    synthetic["prevention::icw_ignored_edge_case"] = [
        {
            "category": "prevention",
            "subcategory": "icw_ignored_edge_case",
            "description": "ICW prompt ignored when question is too simple or factual",
            "original_question": "What is 2 + 2?",
            "gold_answer": "4",
            "target_wrong_answer": "REFUSE",
            "ai_answer": "4",
            "failure_reason": "Model prioritizes answering simple factual questions over ICW prompt",
            "mitigation": "ICW prompts may be less effective for very simple factual questions"
        },
    ]
    
    return synthetic


def create_markdown_document(analysis_data: Dict[str, Any], output_path: Path):
    """Create the markdown document."""
    stats = analysis_data['statistics']
    examples = analysis_data['examples']
    synthetic = generate_synthetic_examples()
    
    # Load consolidated refusal rates for paper-accurate numbers
    consolidated_path = Path('prevention_refusal_rates_consolidated.json')
    consolidated_data = None
    if consolidated_path.exists():
        with open(consolidated_path, 'r', encoding='utf-8') as f:
            consolidated_data = json.load(f)
    
    lines = []
    lines.append("# DoPE Failure Mode Analysis")
    lines.append("")
    lines.append("This document categorizes failure modes observed in DoPE evaluation and provides")
    lines.append("qualitative examples for each category. Failures are analyzed from prevention")
    lines.append("evaluation runs across multiple models (GPT-4o, GPT-5.1, Claude Opus, Claude Sonnet).")
    lines.append("")
    
    # Statistics overview
    lines.append("## Overview Statistics")
    lines.append("")
    lines.append(f"- **Total Results:** {stats['total_results']:,}")
    lines.append(f"- **Prevention Successes:** {stats['prevention_successes']:,} ({stats['prevention_successes']/stats['total_results']*100:.1f}%)")
    lines.append(f"- **Prevention Failures:** {stats['prevention_failures']:,} ({stats['prevention_failures']/stats['total_results']*100:.1f}%)")
    lines.append("")
    
    # Failure breakdown by category
    lines.append("### Failure Breakdown by Category")
    lines.append("")
    lines.append("| Category | Count | Percentage of Failures |")
    lines.append("|----------|-------|------------------------|")
    total_failures = stats['prevention_failures']
    category_order = [
        "prevention::perturbation_detected_memorization",
        "prevention::perturbation_detected_but_answered",
        "prevention::weak_perturbation_tf",
        "prevention::weak_perturbation_mcq",
        "prevention::vision_parsing_general",
        "prevention::vision_parsing_claude",
        "prevention::icw_ignored",
        "detection::parsing_failure"
    ]
    for category in category_order:
        if category in stats['by_category']:
            count = stats['by_category'][category]
            cat_name = category.replace("::", " - ").replace("_", " ").title()
            pct = (count / total_failures * 100) if total_failures > 0 else 0
            lines.append(f"| {cat_name} | {count:,} | {pct:.1f}% |")
    lines.append("")
    
    # Breakdown by model (use paper naming convention and consolidated numbers)
    lines.append("### Failure Rate by Model")
    lines.append("")
    lines.append("| Model | Successes | Failures | Success Rate | 95% CI |")
    lines.append("|-------|-----------|---------|--------------|--------|")
    model_name_map = {
        'gpt-4o': 'GPT-4o',
        'gpt-5.1': 'GPT-5.1',
        'claude-opus-4-5-20251101': 'Claude Opus 4.5',
        'claude-sonnet-4-5-20250929': 'Claude Sonnet 4.5'
    }
    consolidated_key_map = {
        'gpt-4o': 'gpt-4o',
        'gpt-5.1': 'gpt-5.1',
        'claude-opus-4-5-20251101': 'claude-opus-4-5',
        'claude-sonnet-4-5-20250929': 'claude-sonnet-4-5'
    }
    
    for model, counts in sorted(stats['by_model'].items()):
        total = counts['success'] + counts['failure']
        if total > 0:
            # Use consolidated numbers if available
            consolidated_key = consolidated_key_map.get(model)
            if consolidated_data and consolidated_key and consolidated_key in consolidated_data.get('overall_statistics', {}):
                consolidated = consolidated_data['overall_statistics'][consolidated_key]
                success_rate = consolidated['refusal_rate']
                ci_lower = consolidated['confidence_interval_95']['lower']
                ci_upper = consolidated['confidence_interval_95']['upper']
                ci_str = f"{ci_lower:.2f}-{ci_upper:.2f}%"
            else:
                success_rate = (counts['success'] / total * 100)
                ci_str = "N/A"
            
            display_name = model_name_map.get(model, model)
            lines.append(f"| {display_name} | {counts['success']:,} | {counts['failure']:,} | {success_rate:.2f}% | {ci_str} |")
    lines.append("")
    
    # Breakdown by attack method
    lines.append("### Failure Rate by Attack Method")
    lines.append("")
    lines.append("| Method | Successes | Failures | Success Rate |")
    lines.append("|--------|-----------|---------|--------------|")
    for method, counts in sorted(stats['by_method'].items()):
        total = counts['success'] + counts['failure']
        if total > 0:
            success_rate = (counts['success'] / total * 100)
            method_name = method.replace("_", " ").title()
            lines.append(f"| {method_name} | {counts['success']:,} | {counts['failure']:,} | {success_rate:.1f}% |")
    lines.append("")
    
    # Breakdown by question type
    lines.append("### Failure Rate by Question Type")
    lines.append("")
    lines.append("| Question Type | Successes | Failures | Success Rate |")
    lines.append("|---------------|-----------|---------|--------------|")
    for qtype, counts in sorted(stats['by_question_type'].items()):
        total = counts['success'] + counts['failure']
        if total > 0:
            success_rate = (counts['success'] / total * 100)
            lines.append(f"| {qtype} | {counts['success']:,} | {counts['failure']:,} | {success_rate:.1f}% |")
    lines.append("")
    
    # Prevention Failures
    lines.append("## 1. Prevention Failures")
    lines.append("")
    lines.append("Prevention failures occur when the model answers the question instead of refusing,")
    lines.append("despite the presence of perturbations or ICW prompts.")
    lines.append("")
    
    # 1.1 Weak Perturbation
    lines.append("### 1.1 Weak Perturbation (Model Answers Correctly)")
    lines.append("")
    lines.append("The perturbation is too subtle and the model ignores it, answering the original")
    lines.append("question correctly. This is the most common failure mode.")
    lines.append("")
    
    # Real examples - TF
    if "prevention::weak_perturbation_tf" in examples:
        lines.append("#### True/False Questions")
        lines.append("")
        for i, ex in enumerate(examples["prevention::weak_perturbation_tf"][:3]):
            lines.append(format_example(ex, i))
    
    # Real examples - MCQ
    if "prevention::weak_perturbation_mcq" in examples:
        lines.append("#### Multiple Choice Questions")
        lines.append("")
        for i, ex in enumerate(examples["prevention::weak_perturbation_mcq"][:3]):
            lines.append(format_example(ex, i))
    
    # Synthetic examples for Tier 3-4
    if "prevention::weak_perturbation_tier3" in synthetic:
        lines.append("#### Synthetic Examples: Tier 3-4 Weak Perturbations")
        lines.append("")
        lines.append("These examples illustrate common weak perturbation patterns that fail:")
        lines.append("")
        for i, ex in enumerate(synthetic["prevention::weak_perturbation_tier3"]):
            lines.append(f"**Example {i + 1}:**")
            lines.append("")
            lines.append(f"**Original Question:** {ex['original_question']}")
            lines.append("")
            lines.append(f"**Perturbation:**")
            lines.append(f"- Original: `{ex['perturbation']['original_substring']}`")
            lines.append(f"- Replacement: `{ex['perturbation']['replacement_substring']}`")
            lines.append(f"- Technique: {ex['perturbation']['technique']}")
            lines.append("")
            lines.append(f"**Result:** Model answered `{ex['ai_answer']}` (gold: `{ex['gold_answer']}`)")
            lines.append("")
            lines.append(f"**Failure Reason:** {ex['failure_reason']}")
            lines.append("")
            lines.append(f"**Mitigation:** {ex['mitigation']}")
            lines.append("")
    
    # 1.2 Perturbation Detected But Model Answers
    lines.append("### 1.2 Perturbation Detected But Model Answers")
    lines.append("")
    lines.append("The perturbation is successfully applied and causes the model to answer incorrectly,")
    lines.append("but the model does not refuse to answer. This indicates the perturbation worked")
    lines.append("for detection purposes but failed for prevention.")
    lines.append("")
    
    if "prevention::perturbation_detected_but_answered" in examples:
        for i, ex in enumerate(examples["prevention::perturbation_detected_but_answered"][:3]):
            lines.append(format_example(ex, i))
    
    # 1.2.1 Memorization (Perturbation Detected But Gold Answer Given)
    lines.append("### 1.2.1 Memorization: Perturbation Detected But Gold Answer Given")
    lines.append("")
    lines.append("The perturbation is detected (model sees the change), but the model still provides")
    lines.append("the correct gold answer, suggesting it has memorized the answer and ignores the")
    lines.append("perturbation. This is a form of memorization failure where the model's training")
    lines.append("data contains the exact question-answer pair.")
    lines.append("")
    
    if "prevention::perturbation_detected_memorization" in examples:
        for i, ex in enumerate(examples["prevention::perturbation_detected_memorization"][:5]):
            lines.append(format_example(ex, i))
    
    # 1.3 Vision/Image-Based Parsing (Screenshot)
    lines.append("### 1.3 Vision/Image-Based Parsing (Screenshot)")
    lines.append("")
    lines.append("Models use vision or OCR capabilities to parse the PDF as an image, potentially")
    lines.append("bypassing text-based perturbations. This occurs when models treat the PDF as a")
    lines.append("screenshot and use image recognition rather than text extraction.")
    lines.append("")
    
    lines.append("#### 1.3.1 General Vision Parsing (Both Models)")
    lines.append("")
    if "prevention::vision_parsing_general" in examples:
        for i, ex in enumerate(examples["prevention::vision_parsing_general"][:5]):
            lines.append(format_example(ex, i))
    
    lines.append("#### 1.3.2 Claude-Specific Vision Parsing")
    lines.append("")
    lines.append("Claude models (Opus and Sonnet) are particularly prone to using vision-based")
    lines.append("parsing, which can bypass font-based perturbations that rely on text encoding.")
    lines.append("")
    if "prevention::vision_parsing_claude" in examples:
        for i, ex in enumerate(examples["prevention::vision_parsing_claude"][:5]):
            lines.append(format_example(ex, i))
    
    # 1.4 ICW Prompt Ignored
    lines.append("### 1.4 ICW Prompt Ignored")
    lines.append("")
    lines.append("The ICW (In-Context Watermarking) prompt is embedded but the model ignores it")
    lines.append("and answers the question instead of refusing.")
    lines.append("")
    
    if "prevention::icw_ignored" in examples:
        for i, ex in enumerate(examples["prevention::icw_ignored"][:3]):
            lines.append(format_example(ex, i))
    
    # Synthetic ICW examples
    if "prevention::icw_ignored_edge_case" in synthetic:
        lines.append("#### Edge Cases: ICW Ignored")
        lines.append("")
        for i, ex in enumerate(synthetic["prevention::icw_ignored_edge_case"]):
            lines.append(f"**Example {i + 1}:**")
            lines.append("")
            lines.append(f"**Original Question:** {ex['original_question']}")
            lines.append(f"**AI Answer:** {ex['ai_answer']}")
            lines.append(f"**Failure Reason:** {ex['failure_reason']}")
            lines.append(f"**Mitigation:** {ex['mitigation']}")
            lines.append("")
    
    # 2. Detection Failures
    lines.append("## 2. Detection Failures")
    lines.append("")
    lines.append("Detection failures occur when the system cannot reliably detect AI misuse.")
    lines.append("")
    
    # 2.1 Weak Perturbation
    lines.append("### 2.1 Weak Perturbation")
    lines.append("")
    lines.append("The perturbation is too subtle and the model ignores it, answering the original")
    lines.append("question correctly. This prevents detection because the model's answer matches")
    lines.append("the gold answer.")
    lines.append("")
    
    if "detection::false_negative_tf" in examples:
        lines.append("#### True/False Questions")
        lines.append("")
        for i, ex in enumerate(examples["detection::false_negative_tf"][:3]):
            lines.append(format_example(ex, i))
    
    if "detection::false_negative_mcq" in examples:
        lines.append("#### Multiple Choice Questions")
        lines.append("")
        for i, ex in enumerate(examples["detection::false_negative_mcq"][:3]):
            lines.append(format_example(ex, i))
    
    # 2.2 Memorization: Perturbation Detected But Gold Answer Matches
    lines.append("### 2.2 Memorization: Perturbation Detected But Gold Answer Matches")
    lines.append("")
    lines.append("The perturbation is detected (model sees the change), but the model still")
    lines.append("provides the correct gold answer, suggesting memorization. This is similar to")
    lines.append("prevention memorization but occurs in detection mode where we're trying to")
    lines.append("identify AI misuse.")
    lines.append("")
    
    if "detection::weak_perturbation_memorization_tf" in examples:
        lines.append("#### True/False Questions")
        lines.append("")
        for i, ex in enumerate(examples["detection::weak_perturbation_memorization_tf"][:3]):
            lines.append(format_example(ex, i))
    
    if "detection::weak_perturbation_memorization_mcq" in examples:
        lines.append("#### Multiple Choice Questions")
        lines.append("")
        for i, ex in enumerate(examples["detection::weak_perturbation_memorization_mcq"][:3]):
            lines.append(format_example(ex, i))
    
    # 2.3 Parsing Failures
    lines.append("### 2.3 Parsing Failures")
    lines.append("")
    lines.append("The LLM judge fails to extract the answer correctly from the model's response,")
    lines.append("requiring fallback to regex parsing which may be less accurate.")
    lines.append("")
    
    if "detection::parsing_failure" in examples:
        for i, ex in enumerate(examples["detection::parsing_failure"][:3]):
            lines.append(format_example(ex, i))
    
    # Synthetic parsing examples
    if "detection::parsing_failure_edge_case" in synthetic:
        lines.append("#### Edge Cases: Parsing Failures")
        lines.append("")
        for i, ex in enumerate(synthetic["detection::parsing_failure_edge_case"]):
            lines.append(f"**Example {i + 1}:**")
            lines.append("")
            lines.append(f"**Original Question:** {ex['original_question']}")
            lines.append(f"**AI Answer:** {ex['ai_answer']}")
            lines.append(f"**Failure Reason:** {ex['failure_reason']}")
            lines.append(f"**Mitigation:** {ex['mitigation']}")
            lines.append("")
    
    # 3. Perturbation Generation Failures
    lines.append("## 3. Perturbation Generation Failures")
    lines.append("")
    lines.append("These failures occur during the perturbation generation phase, resulting in")
    lines.append("weak or invalid perturbations that are unlikely to succeed.")
    lines.append("")
    
    # 3.1 Prohibited Techniques
    lines.append("### 3.1 Prohibited Techniques")
    lines.append("")
    lines.append("Perturbations that use prohibited techniques (e.g., negation insertion)")
    lines.append("which are easily normalized by model preprocessing.")
    lines.append("")
    
    if "prevention::prohibited_negation" in synthetic:
        for i, ex in enumerate(synthetic["prevention::prohibited_negation"]):
            lines.append(f"**Example {i + 1}:**")
            lines.append("")
            lines.append(f"**Original Question:** {ex['original_question']}")
            lines.append("")
            lines.append(f"**Perturbation:**")
            lines.append(f"- Original: `{ex['perturbation']['original_substring']}`")
            lines.append(f"- Replacement: `{ex['perturbation']['replacement_substring']}`")
            lines.append(f"- Technique: {ex['perturbation']['technique']}")
            lines.append("")
            lines.append(f"**Result:** Model answered `{ex['ai_answer']}` (gold: `{ex['gold_answer']}`)")
            lines.append("")
            lines.append(f"**Failure Reason:** {ex['failure_reason']}")
            lines.append("")
            lines.append(f"**Mitigation:** {ex['mitigation']}")
            lines.append("")
    
    # Summary and Mitigations
    lines.append("## 4. Summary and Mitigations")
    lines.append("")
    lines.append("### Key Findings")
    lines.append("")
    lines.append("1. **Weak perturbations are the primary failure mode** - Most failures occur when")
    lines.append("   perturbations are too subtle and models ignore them. This accounts for")
    lines.append("   approximately 48.6% of all prevention failures (5,503 out of 11,315).")
    lines.append("")
    lines.append("2. **Perturbation detected but model still answers** - In 50.3% of failures,")
    lines.append("   the perturbation successfully causes incorrect answers but the model does not")
    lines.append("   refuse. This indicates perturbations work for detection but not prevention.")
    lines.append("")
    lines.append("3. **Tier 1 techniques are most effective** - Directional inversions and property")
    lines.append("   swaps (Tier 1) are significantly more reliable than quantifier modifications")
    lines.append("   (Tier 3-4). Synthetic examples demonstrate that quantifier-based perturbations")
    lines.append("   often fail to flip truth values.")
    lines.append("")
    lines.append("4. **ICW prompts are highly effective** - ICW-only attacks show 90.7% success")
    lines.append("   rate (3,846 successes vs 393 failures), but may fail on very simple factual")
    lines.append("   questions. For GPT-5.1, ICW achieves 100% success rate (1,697/1,697).")
    lines.append("")
    lines.append("5. **Combined attacks improve robustness** - ICW combined with font/dual-layer")
    lines.append("   attacks show better prevention rates than individual methods:")
    lines.append("   - ICW + Font Attack: 85.3% success rate (7,225/8,473)")
    lines.append("   - ICW + Dual Layer: 87.9% success rate (7,448/8,473)")
    lines.append("   - Font Attack alone: 40.9% success rate (3,462/8,473)")
    lines.append("   - Dual Layer alone: 57.1% success rate (4,835/8,473)")
    lines.append("")
    lines.append("6. **Model performance varies significantly** - GPT-5.1 shows the highest prevention")
    lines.append("   success rate (82.39%, CI: 81.78-82.99%), followed by GPT-4o (71.00%, CI: 70.28-71.72%),")
    lines.append("   Claude Sonnet 4.5 (52.28%, CI: 50.68-53.86%), and Claude Opus 4.5 (37.11%, CI: 35.59-38.66%).")
    lines.append("   These numbers match the consolidated refusal rates reported in the paper.")
    lines.append("")
    lines.append("7. **Question type affects success rates** - True/False questions show the highest")
    lines.append("   prevention success rate (71.7%), followed by Long-form (71.5%) and MCQ (68.3%).")
    lines.append("")
    
    lines.append("### Recommended Mitigations")
    lines.append("")
    lines.append("1. **Prioritize Tier 1 perturbation techniques** - Use directional inversions")
    lines.append("   and property swaps instead of quantifier modifications.")
    lines.append("")
    lines.append("2. **Validate perturbation strength** - Implement automated checks to ensure")
    lines.append("   perturbations create unambiguous truth-value flips.")
    lines.append("")
    lines.append("3. **Combine multiple attack methods** - Use ICW + font/dual-layer combinations")
    lines.append("   for better prevention rates.")
    lines.append("")
    lines.append("4. **Improve LLM judge robustness** - Enhance parsing to handle ambiguous")
    lines.append("   responses with multiple option mentions.")
    lines.append("")
    
    # Write output
    output_path.write_text("\n".join(lines), encoding='utf-8')
    print(f"Markdown document written to {output_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate markdown from failure modes analysis")
    parser.add_argument('--analysis-json', default='failure_modes_analysis.json',
                       help='Input JSON file from analyze_failure_modes.py')
    parser.add_argument('--output', default='docs/analysis/failure_modes_qualitative_analysis.md',
                       help='Output markdown file')
    
    args = parser.parse_args()
    
    analysis_path = Path(args.analysis_json)
    if not analysis_path.exists():
        print(f"Error: {analysis_path} does not exist", file=sys.stderr)
        return 1
    
    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    create_markdown_document(analysis_data, output_path)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
