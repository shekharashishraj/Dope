"""Grouped TF batch prompt - instructions once, all questions listed together."""
from typing import Dict, List, Any


TF_GROUPED_BATCH_TEMPLATE = """You are an expert at generating text substitutions for True/False questions that reliably flip the truth value. Your accuracy is critical.

## INSTRUCTIONS (apply to ALL questions below)

**Strategy:** Replacement (replace exactly ONE contiguous substring in the stem)

**CRITICAL HARD CONSTRAINTS (must satisfy ALL - verify each mapping):**
1) Single-span edit: replace exactly ONE contiguous substring inside latex_stem_text (stem only, no multiple edits).
2) Exact match: original_substring MUST be found verbatim in latex_stem_text (character-for-character, including all LaTeX commands, spaces, special characters).
3) Valid indices: latex_stem_text[start_pos:end_pos] == original_substring EXACTLY AND end_pos = start_pos + len(original_substring) EXACTLY.
4) Non-empty strings: Both original_substring and replacement_substring MUST contain actual text (no empty strings, no whitespace-only).
5) Different strings: replacement_substring MUST be different from original_substring (no identical mappings).
6) Length constraint: len(replacement_substring) <= len(original_substring) is MANDATORY (prevents layout issues).
7) Truth flip: target_wrong_answer MUST be exactly the opposite of gold_answer (if gold is "True", target must be "False", and vice versa).
8) Non-trivial change: replacement must make the statement CLEARLY switch truth value (not just wording - must be verifiable factual flip).
9) Zero-negation rule: DO NOT rely on inserting/removing "not/never/no". Prefer changing key term, condition, quantifier, number, direction, scope, or entity.
10) Layout-safe: replacement_substring should be similar length to original_substring (aim: within ±12 characters) and keep LaTeX well-formed.
11) Semantic quality: Replacement must be natural and semantically meaningful (not awkward phrasing).

## TRUTH-FLIPPING TECHNIQUES (Ranked by Effectiveness)

**Tier 1 - Comparative/Directional Inversion (Best):**
- "increases" ↔ "decreases"
- "greater than" ↔ "less than"
- "before" ↔ "after"
- "positive" ↔ "negative"
- "clockwise" ↔ "counterclockwise"

**Tier 2 - Property/State Swap:**
- "endothermic" ↔ "exothermic"
- "acidic" ↔ "basic"
- "conductor" ↔ "insulator"
- "soluble" ↔ "insoluble"
- "dominant" ↔ "recessive"

**Tier 3 - Quantifier Modification:**
- "always" → "sometimes" (True→False)
- "all" → "some" or "most"
- "never" → "rarely"
- "every" → "most"

**Tier 4 - Entity/Value Substitution:**
- Swap one correct entity for a related but incorrect one
- Change numerical values to incorrect ones
- Replace correct formula/equation component

## PROHIBITED TECHNIQUES (Will Be Rejected)

❌ **Negation insertion**: "is" → "is not", "can" → "cannot", adding "un-", "non-", "in-"
❌ **Double negatives**: Any construction that adds negative particles
❌ **Trivial additions**: "true" → "false", "correct" → "incorrect"
❌ **Identity mappings**: original == replacement

**What to output for each mapping:**
- question_index: The question number
- latex_stem_text: Must exactly equal the input latex_stem_text
- original_substring: The substring to replace
- replacement_substring: The replacement text
- start_pos: Start position (0-based)
- end_pos: End position (exclusive)
- target_wrong_answer: "True" or "False" (the flipped label - must be opposite of gold_answer)
- reasoning: 1–2 sentences explaining why the truth value flips after the replacement
- verification: Causal chain showing original → replacement → factual change → truth flip

**VALIDATION CHECKLIST (verify each mapping before including):**
✓ original_substring exists verbatim in latex_stem_text
✓ latex_stem_text[start_pos:end_pos] == original_substring exactly
✓ end_pos == start_pos + len(original_substring) exactly
✓ replacement_substring != original_substring (different strings)
✓ len(replacement_substring) > 0 and len(original_substring) > 0 (non-empty)
✓ len(replacement_substring) <= len(original_substring) (length constraint)
✓ target_wrong_answer is exactly opposite of gold_answer (True↔False)
✓ NO negation words added ("not", "un-", "non-", "in-", "cannot", etc.)
✓ Perturbation uses Tier 1 or Tier 2 techniques (directional inversion, property swap)
✓ Replacement causes verifiable truth-value flip (not trivial negation)
✓ Replacement is natural and semantically meaningful

## TF QUESTIONS

{questions_list}

## OUTPUT FORMAT

Return ONLY valid JSON as a single array containing ALL mappings from ALL questions above.
Each question should have {k} mappings.

Total expected mappings: {total_mappings}

```json
[
  {{
    "question_index": 3,
    "latex_stem_text": "...",
    "original_substring": "...",
    "replacement_substring": "...",
    "start_pos": 0,
    "end_pos": 5,
    "target_wrong_answer": "False",
    "reasoning": "...",
    "verification": "'increases' → 'decreases' → violates 2nd law of thermodynamics → statement becomes False"
  }},
  ...
]
```

Return ONLY valid JSON array, no markdown fences, no additional commentary."""


def format_tf_question_entry(
    question_index: int,
    latex_stem_text: str,
    copyable_text: str,
    gold_answer: str
) -> str:
    """Format a single TF question entry for grouped batch prompt."""
    flipped_answer = "False" if gold_answer == "True" else "True"
    return f"""**Question {question_index}:**
- LaTeX stem: `{latex_stem_text}`
- Copyable text: {copyable_text}
- Gold answer: {gold_answer} (must flip to {flipped_answer})
- Goal: Generate 3 mappings that flip the truth value (use Tier 1-2 techniques, NO negations)

"""


def format_grouped_tf_batch(
    questions: List[Dict[str, Any]],
    k: int = 3
) -> str:
    """
    Format grouped TF batch prompt.
    
    Args:
        questions: List of question dicts with keys: question_index, latex_stem_text, 
                   copyable_text, gold_answer
        k: Number of mappings per question (default: 3)
    
    Returns:
        Formatted grouped batch prompt
    """
    questions_list = []
    for q in questions:
        questions_list.append(format_tf_question_entry(
            question_index=q['question_index'],
            latex_stem_text=q['latex_stem_text'],
            copyable_text=q['copyable_text'],
            gold_answer=q['gold_answer']
        ))
    
    total_mappings = len(questions) * k
    
    return TF_GROUPED_BATCH_TEMPLATE.format(
        questions_list="\n".join(questions_list),
        k=k,
        total_mappings=total_mappings
    )
