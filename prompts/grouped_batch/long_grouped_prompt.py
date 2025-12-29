"""Grouped LONG batch prompt - instructions once, all questions listed together."""
from typing import Dict, List, Any


LONG_GROUPED_BATCH_TEMPLATE = """You are an expert at generating minimal, high-impact text substitutions for long-form questions (essay, short answer, etc.).

## INSTRUCTIONS (apply to ALL questions below)

**Strategy:** Replacement (replace exactly ONE contiguous substring in the stem)

**Hard constraints (must satisfy all):**
1) Single-span edit: replace exactly one contiguous substring inside latex_stem_text (stem only).
2) Exact match: original_substring must be an exact substring of latex_stem_text (character-for-character, including LaTeX).
3) Valid indices: latex_stem_text[start_pos:end_pos] == original_substring AND end_pos = start_pos + len(original_substring).
4) Non-trivial change: replacement must change the question focus in a way that affects the expected answer.
5) Avoid trivial negation: do not flip with a simple "not/never/no" insertion; prefer changing a key concept, condition, quantity, direction, scope, or referent.
6) Layout-safe: replacement_substring should be similar length to original_substring (aim: within ±12 characters) and keep LaTeX well-formed.
7) Distinctness: mappings should not be near-duplicates; vary the edited span and/or the targeted answer.

**What to output for each mapping:**
- question_index: The question number
- latex_stem_text: Must exactly equal the input latex_stem_text
- original_substring: The substring to replace
- replacement_substring: The replacement text
- start_pos: Start position (0-based)
- end_pos: End position (exclusive)
- target_wrong_answer: Description of how the answer should deviate (e.g., "focuses on different aspect", "changes key concept")
- reasoning: 1–2 sentences explaining why this mapping causes deviation

## LONG QUESTIONS

{questions_list}

## OUTPUT FORMAT

Return ONLY valid JSON as a single array containing ALL mappings from ALL questions above.
Each question should have {k} mappings.

Total expected mappings: {total_mappings}

[
  {{"question_index": 1, "latex_stem_text": "...", "original_substring": "...", "replacement_substring": "...", "start_pos": 0, "end_pos": 5, "target_wrong_answer": "focuses on different aspect", "reasoning": "..."}},
  ...
]

Return ONLY valid JSON array, no markdown or additional text."""


def format_long_question_entry(
    question_index: int,
    latex_stem_text: str,
    copyable_text: str,
    gold_answer: str
) -> str:
    """Format a single LONG question entry for grouped batch prompt."""
    return f"""**Question {question_index}:**
- LaTeX stem: `{latex_stem_text}`
- Copyable text: {copyable_text}
- Gold answer: {gold_answer}
- Goal: Generate 3 mappings that cause verifiable deviation from the gold answer

"""


def format_grouped_long_batch(
    questions: List[Dict[str, Any]],
    k: int = 3
) -> str:
    """
    Format grouped LONG batch prompt.
    
    Args:
        questions: List of question dicts with keys: question_index, latex_stem_text, 
                   copyable_text, gold_answer
        k: Number of mappings per question (default: 3)
    
    Returns:
        Formatted grouped batch prompt
    """
    questions_list = []
    for q in questions:
        questions_list.append(format_long_question_entry(
            question_index=q['question_index'],
            latex_stem_text=q['latex_stem_text'],
            copyable_text=q['copyable_text'],
            gold_answer=q['gold_answer']
        ))
    
    total_mappings = len(questions) * k
    
    return LONG_GROUPED_BATCH_TEMPLATE.format(
        questions_list="\n".join(questions_list),
        k=k,
        total_mappings=total_mappings
    )

