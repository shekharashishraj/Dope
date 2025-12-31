"""Grouped MCQ batch prompt - instructions once, all questions listed together."""
from typing import Dict, List, Any


MCQ_GROUPED_BATCH_TEMPLATE = """You are an expert at generating text substitutions for academic multiple-choice questions that cause predictable answer shifts. Your accuracy is critical.

## INSTRUCTIONS (apply to ALL questions below)

**Strategy:** Replacement (replace exactly ONE contiguous substring in the stem)

**CRITICAL HARD CONSTRAINTS (must satisfy ALL - verify each mapping):**
1) Single-span edit: replace exactly ONE contiguous substring inside latex_stem_text (the stem only; do NOT edit the options, no multiple edits).
2) Exact match: original_substring MUST be found verbatim in latex_stem_text (character-for-character, including all LaTeX commands, spaces, special characters).
3) Valid indices: latex_stem_text[start_pos:end_pos] == original_substring EXACTLY AND end_pos = start_pos + len(original_substring) EXACTLY.
4) Non-empty strings: Both original_substring and replacement_substring MUST contain actual text (no empty strings, no whitespace-only).
5) Different strings: replacement_substring MUST be different from original_substring (no identical mappings).
6) Length constraint: len(replacement_substring) <= len(original_substring) is MANDATORY (prevents layout issues).
7) Answer change: target_wrong_answer MUST be different from the gold answer (each mapping should ideally target a different wrong option).
8) Non-trivial change: replacement must change the meaning enough to CLEARLY flip the correct answer; avoid purely grammatical rephrases.
9) Avoid trivial negation: DO NOT flip with simple "not/never/no" insertion. Prefer changing key concept, condition, quantity, direction, scope, or referent.
10) Layout-safe: replacement_substring should be similar length to original_substring (aim: within ±12 characters) and keep LaTeX well-formed.
11) Distinctness: mappings should not be near-duplicates; vary the edited span and/or the targeted answer.
12) Semantic quality: Replacement must be natural and semantically meaningful (not awkward phrasing).

## QUALITY TIERS (aim for Tier 1)

**Tier 1 (Best):** Changes a core entity, parameter, condition, or relationship that fundamentally alters what's being asked.
Example: "maximum" → "minimum", "increases" → "decreases", "before" → "after", "India" → "China"

**Tier 2 (Acceptable):** Changes scope, quantity, or specificity. 
Example: "all" → "one", "primary" → "secondary", "first" → "last", "global" → "local"

**Tier 3 (Weak - Avoid):** Surface-level word swaps that don't reliably shift answers.
Example: synonyms, minor qualifiers

**What to output for each mapping:**
- question_index: The question number
- latex_stem_text: Must exactly equal the input latex_stem_text
- original_substring: The substring to replace
- replacement_substring: The replacement text
- start_pos: Start position (0-based)
- end_pos: End position (exclusive)
- target_wrong_answer: A single option key (e.g., "A", "B", "C", "D") that is NOT the gold answer
- reasoning: 1–2 sentences explaining why the new stem makes target_wrong_answer correct and the gold answer incorrect
- verification: Causal chain showing original → replacement → interpretation → answer selection

**VALIDATION CHECKLIST (verify each mapping before including):**
✓ original_substring exists verbatim in latex_stem_text
✓ latex_stem_text[start_pos:end_pos] == original_substring exactly
✓ end_pos == start_pos + len(original_substring) exactly
✓ replacement_substring != original_substring (different strings)
✓ len(replacement_substring) > 0 and len(original_substring) > 0 (non-empty)
✓ len(replacement_substring) <= len(original_substring) (length constraint)
✓ target_wrong_answer != gold_answer (different option)
✓ Perturbation is Tier 1 or Tier 2 quality
✓ Replacement changes meaning enough to flip answer (not trivial negation)
✓ Replacement is natural and semantically meaningful

## MCQ QUESTIONS

{questions_list}

## OUTPUT FORMAT

Return ONLY valid JSON as a single array containing ALL mappings from ALL questions above.
Each question should have {k} mappings (one for each target wrong answer).

Total expected mappings: {total_mappings}

```json
[
  {{
    "question_index": 1,
    "latex_stem_text": "...",
    "original_substring": "...",
    "replacement_substring": "...",
    "start_pos": 0,
    "end_pos": 5,
    "target_wrong_answer": "B",
    "reasoning": "...",
    "verification": "'primary function' → 'least common role' → reader seeks rare function → selects C"
  }},
  ...
]
```

Return ONLY valid JSON array, no markdown fences, no additional commentary."""


def format_mcq_question_entry(
    question_index: int,
    latex_stem_text: str,
    copyable_text: str,
    gold_answer: str,
    options: Dict[str, str]
) -> str:
    """Format a single MCQ question entry for grouped batch prompt."""
    options_str = "\n".join([f"  - {key}: {value}" for key, value in options.items()])
    return f"""**Question {question_index}:**
- LaTeX stem: `{latex_stem_text}`
- Copyable text: {copyable_text}
- Gold answer: {gold_answer}
- Options:
{options_str}
- Goal: Generate 3 mappings that each make a DIFFERENT option become correct (change answer away from {gold_answer}, use Tier 1-2 techniques)

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
