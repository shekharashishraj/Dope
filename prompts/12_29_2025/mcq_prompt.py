"""MCQ perturbation prompt template."""
from typing import Dict, Any

MCQ_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating minimal, high-impact text substitutions for academic multiple-choice questions (MCQ).

Context (do not modify):
- LaTeX question stem: {latex_stem_text}
- Options (unchanged): {options}
- Gold answer (currently correct): {gold_answer}
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
Produce {k} replacement mappings that each make a DIFFERENT option become correct (i.e., change the correct answer away from {gold_answer} to some target_wrong_answer in the provided options).

Hard constraints (must satisfy all):
1) Single-span edit: replace exactly one contiguous substring inside latex_stem_text (the stem only; do NOT edit the options).
2) Exact match: original_substring must be an exact substring of latex_stem_text (character-for-character, including LaTeX).
3) Valid indices: latex_stem_text[start_pos:end_pos] == original_substring AND end_pos = start_pos + len(original_substring).
4) Non-trivial change: replacement must change the meaning enough to flip the correct answer; avoid purely grammatical rephrases.
5) Avoid trivial negation: do not flip with a simple "not/never/no" insertion unless it is the only natural way; prefer changing a key concept, condition, quantity, direction, scope, or referent.
6) Layout-safe: replacement_substring should be similar length to original_substring (aim: within ±12 characters) and keep LaTeX well-formed.
7) Distinctness: mappings should not be near-duplicates; vary the edited span and/or the targeted answer.

What to output for each mapping:
- question_index: {question_index}
- latex_stem_text: must exactly equal the input latex_stem_text
- original_substring
- replacement_substring
- start_pos (0-based)
- end_pos (exclusive)
- target_wrong_answer: a single option key (e.g., "A", "B", "C", "D") that is NOT {gold_answer}
- reasoning: 1–2 sentences explaining why the new stem makes target_wrong_answer correct and {gold_answer} incorrect

Return ONLY valid JSON as an array of {k} objects, with double quotes, no markdown.
[
  {{
    "question_index": {question_index},
    "latex_stem_text": "...",
    "original_substring": "...",
    "replacement_substring": "...",
    "start_pos": 0,
    "end_pos": 5,
    "target_wrong_answer": "B",
    "reasoning": "..."
  }}
]"""

def format_mcq_prompt(
    latex_stem_text: str,
    copyable_text: str,
    gold_answer: str,
    question_type: str,
    options: Dict[str, str],
    question_index: int,
    k: int = 3,
    reasoning_steps: str = "",
    prefix_note: str = "",
    answer_guidance: str = "",
    retry_instructions: str = ""
) -> str:
    """
    Format MCQ replacement prompt with provided parameters.
    
    Args:
        latex_stem_text: LaTeX code for the question stem
        copyable_text: Plain text version of the question stem
        gold_answer: Correct answer option (e.g., "A", "B")
        question_type: Question type (should be "MCQ")
        options: Dictionary of options (e.g., {"A": "...", "B": "..."})
        question_index: Question number
        k: Number of mappings to generate (default: 3)
        reasoning_steps: LLM thinking/reasoning steps (default: empty)
        prefix_note: Optional prefix note (default: empty)
        answer_guidance: Optional answer guidance (default: empty)
        retry_instructions: Optional retry instructions (default: empty)
    
    Returns:
        Formatted prompt string
    """
    # Format options as a readable string
    options_str = "\n".join([f"{key}: {value}" for key, value in options.items()])
    
    return MCQ_REPLACEMENT_PROMPT_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        copyable_text=copyable_text,
        gold_answer=gold_answer,
        question_type=question_type,
        options=options_str,
        question_index=question_index,
        k=k,
        reasoning_steps=reasoning_steps,
        prefix_note=prefix_note,
        answer_guidance=answer_guidance,
        retry_instructions=retry_instructions
    )
