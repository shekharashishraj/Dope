"""Stage 3: Replacement Generation - Generate the replacement text.

This stage focuses on CREATING THE REPLACEMENT:
- Generate text that will replace the original substring
- Ensure the replacement flips the answer to the target
- Respect length and formatting constraints
"""
from typing import Dict, Optional

from .shared_constraints import (
    NEGATION_RULE,
    LENGTH_CONSTRAINT_MCQ,
    LENGTH_CONSTRAINT_TF,
    LATEX_RULE,
)


# =============================================================================
# STAGE 3: TF REPLACEMENT TEMPLATE
# =============================================================================

STAGE3_TF_TEMPLATE = """Generate replacement text for a True/False question.

## CONTEXT
- Stem: {latex_stem_text}
- Original substring to replace: "{original_substring}"
- Gold answer: {gold_answer}
- Target answer after replacement: {target_answer}

## HARD CONSTRAINTS

{length_constraint}

{negation_rule}

{latex_rule}

## REQUIREMENTS
1. The replacement MUST cause the statement to become {target_answer}
2. The replacement must be a CLEAR factual inversion (not subtle)
3. The result must be grammatically correct
4. The replacement should be natural and semantically meaningful

## EXAMPLES

Good replacements (Tier 1):
- "increases" → "decreases"
- "maximum" → "minimum"
- "positive" → "negative"
- "before" → "after"
- "exothermic" → "endothermic"

Bad replacements (PROHIBITED):
- "is" → "is not" ❌ (negation)
- "true" → "false" ❌ (trivial)
- Adding "un-", "non-" ❌ (negation prefix)

## OUTPUT FORMAT
Return ONLY valid JSON with no additional text:
{{"replacement_substring": "new text to insert"}}
"""


# =============================================================================
# STAGE 3: MCQ REPLACEMENT TEMPLATE
# =============================================================================

STAGE3_MCQ_TEMPLATE = """Generate replacement text for a Multiple Choice question.

## CONTEXT
- Stem: {latex_stem_text}
- Original substring to replace: "{original_substring}"
- Gold answer: {gold_answer}
- Target wrong answer: {target_wrong_answer}
- Options:
{options_str}

## HARD CONSTRAINTS

{length_constraint}

{negation_rule}

{latex_rule}

## REQUIREMENTS
1. The replacement MUST cause option {target_wrong_answer} to become the correct answer
2. The replacement must CLEARLY change what the question is asking
3. The result must be grammatically correct
4. The replacement should be natural and semantically meaningful
5. **LENGTH**: len(replacement) <= len(original) is MANDATORY

## EXAMPLES

Good replacements (Tier 1):
- "France" → "Germany" (to target Berlin instead of Paris)
- "Adding" → "Removing" (to reverse the effect)
- "maximum" → "minimum"
- "first" → "last"
- "increases" → "decreases"

Bad replacements (PROHIBITED):
- "is" → "is not" ❌ (negation)
- Adding "un-", "non-" ❌ (negation prefix)
- Replacement longer than original ❌ (layout issues)

## OUTPUT FORMAT
Return ONLY valid JSON with no additional text:
{{"replacement_substring": "new text to insert"}}
"""


def format_stage3_tf_prompt(
    latex_stem_text: str,
    original_substring: str,
    gold_answer: str,
) -> str:
    """Format Stage 3 prompt for TF questions.
    
    Args:
        latex_stem_text: The question stem text
        original_substring: The substring selected in Stage 2
        gold_answer: The correct answer ("True" or "False")
    
    Returns:
        Formatted prompt string
    """
    target_answer = "False" if gold_answer == "True" else "True"
    
    return STAGE3_TF_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        original_substring=original_substring,
        gold_answer=gold_answer,
        target_answer=target_answer,
        length_constraint=LENGTH_CONSTRAINT_TF,
        negation_rule=NEGATION_RULE,
        latex_rule=LATEX_RULE,
    )


def format_stage3_mcq_prompt(
    latex_stem_text: str,
    original_substring: str,
    gold_answer: str,
    target_wrong_answer: str,
    options: Dict[str, str],
) -> str:
    """Format Stage 3 prompt for MCQ questions.
    
    Args:
        latex_stem_text: The question stem text
        original_substring: The substring selected in Stage 2
        gold_answer: The correct answer option
        target_wrong_answer: The target wrong option from Stage 1
        options: Dictionary of option letter to option text
    
    Returns:
        Formatted prompt string
    """
    options_str = "\n".join([f"  - {key}: {value}" for key, value in options.items()])
    
    return STAGE3_MCQ_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        original_substring=original_substring,
        gold_answer=gold_answer,
        target_wrong_answer=target_wrong_answer,
        options_str=options_str,
        length_constraint=LENGTH_CONSTRAINT_MCQ,
        negation_rule=NEGATION_RULE,
        latex_rule=LATEX_RULE,
    )

