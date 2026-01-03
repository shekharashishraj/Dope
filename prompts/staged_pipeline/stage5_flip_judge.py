"""Stage 5: Flip Verification - LLM Judge to verify the answer flips.

This stage uses an LLM to answer the perturbed question and verify
that the answer matches the target wrong answer.
"""
from typing import Dict, Optional


# =============================================================================
# STAGE 5: TF JUDGE TEMPLATE
# =============================================================================

STAGE5_TF_JUDGE_TEMPLATE = """Answer the following True/False question.

## QUESTION
{perturbed_stem}

## INSTRUCTIONS
- Read the statement carefully
- Determine if it is True or False based on factual accuracy
- Provide ONLY your answer

## OUTPUT FORMAT
Return ONLY valid JSON with no additional text:
{{"answer": "True or False"}}
"""


# =============================================================================
# STAGE 5: MCQ JUDGE TEMPLATE
# =============================================================================

STAGE5_MCQ_JUDGE_TEMPLATE = """Answer the following Multiple Choice question.

## QUESTION
{perturbed_stem}

## OPTIONS
{options_str}

## INSTRUCTIONS
- Read the question carefully
- Select the BEST answer from the options provided
- Provide ONLY the option letter

## OUTPUT FORMAT
Return ONLY valid JSON with no additional text:
{{"answer": "X"}}

Where X is a single option letter (A, B, C, D, or E).
"""


def format_stage5_tf_prompt(perturbed_stem: str) -> str:
    """Format Stage 5 judge prompt for TF questions.
    
    Args:
        perturbed_stem: The question stem after replacement
    
    Returns:
        Formatted prompt string
    """
    return STAGE5_TF_JUDGE_TEMPLATE.format(
        perturbed_stem=perturbed_stem,
    )


def format_stage5_mcq_prompt(
    perturbed_stem: str,
    options: Dict[str, str],
) -> str:
    """Format Stage 5 judge prompt for MCQ questions.
    
    Args:
        perturbed_stem: The question stem after replacement
        options: Dictionary of option letter to option text
    
    Returns:
        Formatted prompt string
    """
    options_str = "\n".join([f"  {key}) {value}" for key, value in options.items()])
    
    return STAGE5_MCQ_JUDGE_TEMPLATE.format(
        perturbed_stem=perturbed_stem,
        options_str=options_str,
    )

