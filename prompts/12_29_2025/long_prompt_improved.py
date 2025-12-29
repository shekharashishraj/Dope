"""Long-form perturbation prompt template."""
from typing import Dict, Any

LONG_FORM_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating minimal, high-impact text substitutions for long-form questions (short answer / essay).

Context (do not modify):
- LaTeX question stem: {latex_stem_text}
- Gold answer (expected response direction): {gold_answer}
- Question type: {question_type}
- Strategy: replacement (replace exactly ONE contiguous substring in the stem)
- Reasoning steps:
{reasoning_steps}
- Copyable stem text (use this exact text when selecting substrings and computing indices):
<<<COPY
{copyable_text}
>>>
{prefix_note}{answer_guidance}{retry_instructions}

Goal:
Produce {k} replacement mappings that change what a correct response should contain, so that an answer aligned with {gold_answer} would be incorrect, incomplete, or misdirected.

Hard constraints (must satisfy all):
1) Single-span edit: replace exactly one contiguous substring inside latex_stem_text (stem only).
2) Exact match: original_substring must be an exact substring of latex_stem_text (character-for-character, including LaTeX).
3) Valid indices: latex_stem_text[start_pos:end_pos] == original_substring AND end_pos = start_pos + len(original_substring).
4) Non-trivial change: replacement must materially shift the required concept, condition, comparison target, or requested explanation—not just rephrasing.
5) Avoid trivial negation: do not flip by adding/removing a lone "not/never/no"; prefer changing the underlying target (e.g., mechanism↔application, cause↔effect, supervised↔unsupervised, increase↔decrease, advantages↔limitations, precision↔recall, etc.).
6) Layout-safe: replacement_substring should be similar length to original_substring (aim: within ±12 characters) and keep LaTeX well-formed.
7) Distinctness: mappings should not be near-duplicates; vary the edited span and/or the intended deviation.

What to output for each mapping:
- question_index: {question_index}
- latex_stem_text: must exactly equal the input latex_stem_text
- original_substring
- replacement_substring
- start_pos (0-based)
- end_pos (exclusive)
- target_wrong_answer: short description of the new expected answer direction (e.g., "focuses on limitations instead of benefits", "asks for counterexample rather than definition")
- reasoning: 1–2 sentences explaining how the replacement changes what constitutes a correct answer

Return ONLY valid JSON as an array of {k} objects, with double quotes, no markdown.
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
  }}
]"""

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

