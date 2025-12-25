"""Long-form perturbation prompt template."""
from typing import Dict, Any


LONG_FORM_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating text substitutions for long-form questions (essay, short answer, etc.).

Given:
- LaTeX code for the question stem: {latex_stem_text}
- Gold answer: {gold_answer}
- Question type: {question_type}
- Strategy: replacement
- Reasoning steps:
{reasoning_steps}
- Copyable text (use this exact text when selecting substrings):
<<<COPY
{copyable_text}
>>>
{prefix_note}{answer_guidance}{retry_instructions}

Your task:
Generate {k} valid mappings that satisfy the replacement strategy. Each mapping should:
1. Replace one contiguous substring of the question stem
2. Cause a verifiable and detectable deviation from the gold answer
3. Ensure the replacement is semantically meaningful and natural
4. Change the question focus in a way that affects the expected answer

### VALIDATION RULES:
- **Good Change**: "economic impact" -> "cultural impact" (Changes the required evidence).
- **Bad Change**: "economic impact" -> "lack of economic impact" (Trivial negation).
- **Constraint**: original_substring must match the LaTeX text exactly.

For each mapping, provide:
1. question_index: The question number ({question_index})
2. latex_stem_text: Exact LaTeX text of the question stem (must match the input exactly)
3. original_substring: The substring to replace (must be a contiguous substring of latex_stem_text)
4. replacement_substring: The replacement text
5. start_pos: Start position of original_substring relative to latex_stem_text (0-based index)
6. end_pos: End position of original_substring relative to latex_stem_text (exclusive, 0-based index)
7. target_wrong_answer: Description of how the answer should deviate (e.g., "focuses on different aspect", "changes key concept")
8. reasoning: Brief explanation of why this mapping satisfies the strategy and how it causes deviation

IMPORTANT:
- The original_substring MUST be an exact substring of latex_stem_text
- The start_pos and end_pos MUST be accurate (start_pos + len(original_substring) = end_pos)
- The replacement should cause a verifiable deviation in the answer
- CRITICAL: The replacement_substring MUST be DIFFERENT from the original_substring. Do NOT generate mappings where original_substring == replacement_substring. The replacement MUST change the text to create actual manipulation.
- CRITICAL: Neither original_substring nor replacement_substring can be empty strings. Both must contain actual text.
- LENGTH CONSTRAINT: The replacement_substring MUST be smaller or equal in length to the original_substring (len(replacement_substring) <= len(original_substring)). This is critical for maintaining document layout and preventing text overflow.
- latex_stem_text is provided exactly as it appears in the LaTeX source. Do NOT trim, normalise, or reformat it when determining positions.
- The latex_stem_text may include \item tokens from enumerate environments. Keep the \item token intact and operate on the descriptive text that follows it whenever possible.
- The replacement should be natural and semantically meaningful

Return as JSON array:
[
  {{
    "question_index": {question_index},
    "latex_stem_text": "...",
    "original_substring": "...",
    "replacement_substring": "...",
    "start_pos": 0,
    "end_pos": 5,
    "target_wrong_answer": "focuses on different aspect",
    "reasoning": "..."
  }},
  ...
]
Return ONLY valid JSON, no markdown or additional text."""


def format_long_prompt(
    latex_stem_text: str,
    copyable_text: str,
    gold_answer: str,
    question_type: str,
    question_index: int,
    k: int = 3,
    reasoning_steps: str = "",
    prefix_note: str = "",
    answer_guidance: str = "",
    retry_instructions: str = ""
) -> str:
    """
    Format long-form replacement prompt with provided parameters.
    
    Args:
        latex_stem_text: LaTeX code for the question stem
        copyable_text: Plain text version of the question stem
        gold_answer: Expected answer description
        question_type: Question type (should be "LONG")
        question_index: Question number
        k: Number of mappings to generate (default: 3)
        reasoning_steps: LLM thinking/reasoning steps (default: empty)
        prefix_note: Optional prefix note (default: empty)
        answer_guidance: Optional answer guidance (default: empty)
        retry_instructions: Optional retry instructions (default: empty)
    
    Returns:
        Formatted prompt string
    """
    return LONG_FORM_REPLACEMENT_PROMPT_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        copyable_text=copyable_text,
        gold_answer=gold_answer,
        question_type=question_type,
        question_index=question_index,
        k=k,
        reasoning_steps=reasoning_steps,
        prefix_note=prefix_note,
        answer_guidance=answer_guidance,
        retry_instructions=retry_instructions
    )

