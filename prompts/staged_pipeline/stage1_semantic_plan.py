"""Stage 1: Semantic Planning - Identify the concept to flip and target answer.

This stage focuses purely on the SEMANTIC decision:
- What concept/property should be changed?
- What is the target wrong answer?

No substring selection or replacement generation happens here.
"""
from typing import Dict, Any

from .shared_constraints import (
    TF_TIER_GUIDANCE,
    TF_PROHIBITED_TECHNIQUES,
    MCQ_TIER_GUIDANCE,
    NEGATION_RULE,
)


# =============================================================================
# STAGE 1: TF TEMPLATE
# =============================================================================

STAGE1_TF_TEMPLATE = """You are identifying a semantic flip strategy for a True/False question.

Your task is to determine:
1. The target wrong answer (opposite of gold)
2. A brief strategy for how to flip the truth value

## QUESTION
- Stem: {latex_stem_text}
- Gold answer: {gold_answer}
- Target: Flip to {target_answer}

{tier_guidance}

{prohibited_techniques}

{negation_rule}

## CRITICAL REQUIREMENTS
- The flip strategy MUST use Tier 1 or Tier 2 techniques
- The flip MUST be unambiguous - after the edit, the statement must CLEARLY be {target_answer}
- NO negation-based flips (no "not", "un-", "non-", etc.)
- The strategy should describe WHAT concept to change, not HOW to change it

## OUTPUT FORMAT
Return ONLY valid JSON with no additional text:
{{"target_wrong_answer": "{target_answer}", "flip_strategy": "1-2 sentence description of what concept/property to change"}}
"""


# =============================================================================
# STAGE 1: MCQ TEMPLATE
# =============================================================================

STAGE1_MCQ_TEMPLATE = """You are identifying a semantic flip strategy for a Multiple Choice question.

Your task is to determine:
1. Which wrong option to target (must NOT be the gold answer)
2. A brief strategy for how to make that option become correct

## QUESTION
- Stem: {latex_stem_text}
- Gold answer: {gold_answer}
- Options:
{options_str}

{tier_guidance}

{negation_rule}

## CRITICAL REQUIREMENTS
- Pick the wrong option that is MOST LIKELY to become correct with a minimal edit
- The flip strategy MUST use Tier 1 techniques (entity/property/direction changes)
- NO negation-based flips (no "not", "un-", "non-", etc.)
- The strategy should describe WHAT concept to change, not HOW to change it
- After the edit, the target option must CLEARLY be the correct answer

## OUTPUT FORMAT
Return ONLY valid JSON with no additional text:
{{"target_wrong_answer": "X", "flip_strategy": "1-2 sentence description of what concept/property to change"}}

Where X is a single option letter (A, B, C, D, E) that is NOT {gold_answer}.
"""


def format_stage1_tf_prompt(
    latex_stem_text: str,
    gold_answer: str,
) -> str:
    """Format Stage 1 prompt for TF questions.
    
    Args:
        latex_stem_text: The question stem text
        gold_answer: The correct answer ("True" or "False")
    
    Returns:
        Formatted prompt string
    """
    target_answer = "False" if gold_answer == "True" else "True"
    
    return STAGE1_TF_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        gold_answer=gold_answer,
        target_answer=target_answer,
        tier_guidance=TF_TIER_GUIDANCE,
        prohibited_techniques=TF_PROHIBITED_TECHNIQUES,
        negation_rule=NEGATION_RULE,
    )


def format_stage1_mcq_prompt(
    latex_stem_text: str,
    gold_answer: str,
    options: Dict[str, str],
) -> str:
    """Format Stage 1 prompt for MCQ questions.
    
    Args:
        latex_stem_text: The question stem text
        gold_answer: The correct answer option (e.g., "A", "B")
        options: Dictionary of option letter to option text
    
    Returns:
        Formatted prompt string
    """
    options_str = "\n".join([f"  - {key}: {value}" for key, value in options.items()])
    
    return STAGE1_MCQ_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        gold_answer=gold_answer,
        options_str=options_str,
        tier_guidance=MCQ_TIER_GUIDANCE,
        negation_rule=NEGATION_RULE,
    )

