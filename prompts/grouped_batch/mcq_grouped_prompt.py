"""Grouped MCQ batch prompt - instructions once, all questions listed together."""
from typing import Dict, List, Any


MCQ_GROUPED_BATCH_TEMPLATE = """You are an expert at generating minimal, high-impact text substitutions for academic multiple-choice questions (MCQ).

## INSTRUCTIONS (apply to ALL questions below)

**Strategy:** Replacement (replace exactly ONE contiguous substring in the stem)

**Hard constraints (must satisfy all):**
1) Single-span edit: replace exactly one contiguous substring inside latex_stem_text (the stem only; do NOT edit the options).
2) Exact match: original_substring must be an exact substring of latex_stem_text (character-for-character, including LaTeX).
3) Valid indices: latex_stem_text[start_pos:end_pos] == original_substring AND end_pos = start_pos + len(original_substring).
4) Non-trivial change: replacement must change the meaning enough to flip the correct answer; avoid purely grammatical rephrases.
5) Avoid trivial negation: do not flip with a simple "not/never/no" insertion unless it is the only natural way; prefer changing a key concept, condition, quantity, direction, scope, or referent.
6) Layout-safe: replacement_substring should be similar length to original_substring (aim: within ±12 characters) and keep LaTeX well-formed.
7) Distinctness: mappings should not be near-duplicates; vary the edited span and/or the targeted answer.

**What to output for each mapping:**
- question_index: The question number
- latex_stem_text: Must exactly equal the input latex_stem_text
- original_substring: The substring to replace
- replacement_substring: The replacement text
- start_pos: Start position (0-based)
- end_pos: End position (exclusive)
- target_wrong_answer: A single option key (e.g., "A", "B", "C", "D") that is NOT the gold answer
- reasoning: 1–2 sentences explaining why the new stem makes target_wrong_answer correct and the gold answer incorrect

## MCQ QUESTIONS

{questions_list}

## OUTPUT FORMAT

Return ONLY valid JSON as a single array containing ALL mappings from ALL questions above.
Each question should have {k} mappings (one for each target wrong answer).

Total expected mappings: {total_mappings}

[
  {{"question_index": 1, "latex_stem_text": "...", "original_substring": "...", "replacement_substring": "...", "start_pos": 0, "end_pos": 5, "target_wrong_answer": "B", "reasoning": "..."}},
  {{"question_index": 1, "latex_stem_text": "...", "original_substring": "...", "replacement_substring": "...", "start_pos": 0, "end_pos": 5, "target_wrong_answer": "C", "reasoning": "..."}},
  {{"question_index": 1, "latex_stem_text": "...", "original_substring": "...", "replacement_substring": "...", "start_pos": 0, "end_pos": 5, "target_wrong_answer": "D", "reasoning": "..."}},
  {{"question_index": 2, "latex_stem_text": "...", "original_substring": "...", "replacement_substring": "...", "start_pos": 0, "end_pos": 5, "target_wrong_answer": "A", "reasoning": "..."}},
  ...
]

Return ONLY valid JSON array, no markdown or additional text."""


def format_mcq_question_entry(
    question_index: int,
    latex_stem_text: str,
    copyable_text: str,
    gold_answer: str,
    options: Dict[str, str]
) -> str:
    """Format a single MCQ question entry for grouped batch prompt."""
    options_str = "\n".join([f"  {key}: {value}" for key, value in options.items()])
    return f"""**Question {question_index}:**
- LaTeX stem: `{latex_stem_text}`
- Copyable text: {copyable_text}
- Gold answer: {gold_answer}
- Options:
{options_str}
- Goal: Generate 3 mappings that each make a DIFFERENT option become correct (change answer away from {gold_answer})

"""


def format_grouped_mcq_batch(
    questions: List[Dict[str, Any]],
    k: int = 3
) -> str:
    """
    Format grouped MCQ batch prompt.
    
    Args:
        questions: List of question dicts with keys: question_index, latex_stem_text, 
                   copyable_text, gold_answer, options
        k: Number of mappings per question (default: 3)
    
    Returns:
        Formatted grouped batch prompt
    """
    questions_list = []
    for q in questions:
        questions_list.append(format_mcq_question_entry(
            question_index=q['question_index'],
            latex_stem_text=q['latex_stem_text'],
            copyable_text=q['copyable_text'],
            gold_answer=q['gold_answer'],
            options=q['options']
        ))
    
    total_mappings = len(questions) * k
    
    return MCQ_GROUPED_BATCH_TEMPLATE.format(
        questions_list="\n".join(questions_list),
        k=k,
        total_mappings=total_mappings
    )

