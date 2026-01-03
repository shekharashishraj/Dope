"""Grouped LONG batch prompt v2 - instructions once, all questions listed together."""
from typing import Dict, List, Any


LONG_GROUPED_BATCH_TEMPLATE = """You are an expert at generating precise, high-impact text substitutions for long-form questions (essay, short answer, explanation) that cause predictable, detectable deviations in responses. Your accuracy is critical.

## INSTRUCTIONS (apply to ALL questions below)

**Strategy:** Replacement (replace exactly ONE contiguous substring in the stem)

**CRITICAL HARD CONSTRAINTS (must satisfy ALL - verify each mapping):**
1) Single-span edit: replace exactly ONE contiguous substring inside latex_stem_text (stem only, no multiple edits).
2) Exact match: original_substring MUST be found verbatim in latex_stem_text (character-for-character, including all LaTeX commands, spaces, special characters).
3) Valid indices: latex_stem_text[start_pos:end_pos] == original_substring EXACTLY AND end_pos = start_pos + len(original_substring) EXACTLY.
4) Non-empty strings: Both original_substring and replacement_substring MUST contain actual text (no empty strings, no whitespace-only).
5) Different strings: replacement_substring MUST be different from original_substring (no identical mappings).
6) Length constraint: len(replacement_substring) <= len(original_substring) is MANDATORY (prevents layout issues).
7) Non-trivial change: replacement must change the question focus in a way that CLEARLY affects the expected answer (different aspect, entity, time period, or concept).
8) Avoid trivial negation: DO NOT flip with simple "not/never/no" insertion. Prefer changing key concept, condition, quantity, direction, scope, or referent.
9) Layout-safe: replacement_substring should be similar length to original_substring (aim: within ±12 characters) and keep LaTeX well-formed.
10) Distinctness: mappings should not be near-duplicates; vary the edited span and/or the targeted answer deviation.
11) Semantic quality: Replacement must be natural and semantically meaningful (not awkward phrasing).

## DEVIATION STRATEGY TIERS

**Tier 1 - Scope/Focus Shift (Best for Detection):**
Changes WHAT the question asks about while keeping the domain.
- "economic impact" → "social impact"
- "causes of" → "effects of"
- "advantages" → "disadvantages"
- "short-term" → "long-term"
- "domestic" → "international"

*Detection signature*: Response discusses entirely different aspect; keyword overlap with gold answer is minimal.

**Tier 2 - Temporal/Contextual Shift:**
Changes WHEN or WHERE the question applies.
- "19th century" → "20th century"
- "in Europe" → "in Asia"
- "during peacetime" → "during wartime"
- "modern" → "historical"

*Detection signature*: Response references different time period, geography, or context.

**Tier 3 - Perspective/Stakeholder Shift:**
Changes WHO or WHOSE viewpoint is requested.
- "from a patient's perspective" → "from a doctor's perspective"
- "for consumers" → "for producers"
- "individual level" → "societal level"
- "scientific view" → "ethical view"

*Detection signature*: Response adopts different analytical framework or stakeholder concerns.

**Tier 4 - Methodological Shift:**
Changes HOW the question should be approached.
- "explain" → "compare"
- "describe" → "evaluate"
- "list" → "analyze"
- "quantitative" → "qualitative"

*Detection signature*: Response structure and content type differs (list vs. analysis, description vs. critique).

## DETECTION SIGNATURE DESIGN

For long-form questions, your `target_wrong_answer` should describe:
1. **Expected content shift**: What topic/aspect the perturbed response will focus on
2. **Detectable markers**: Specific terms, concepts, or structures that will appear
3. **Absence markers**: Key elements from gold answer that will be missing

Example format: "Response will focus on [X] instead of [Y], containing markers like [terms] and lacking [gold answer concepts]"

**What to output for each mapping:**
- question_index: The question number
- latex_stem_text: Must exactly equal the input latex_stem_text
- original_substring: The substring to replace
- replacement_substring: The replacement text
- start_pos: Start position (0-based)
- end_pos: End position (exclusive)
- target_wrong_answer: Description of how the answer should deviate (include content shift, presence markers, absence markers)
- reasoning: 1–2 sentences explaining why this mapping causes deviation
- verification: Causal chain showing original → replacement → content shift → detection method

**VALIDATION CHECKLIST (verify each mapping before including):**
✓ original_substring exists verbatim in latex_stem_text
✓ latex_stem_text[start_pos:end_pos] == original_substring exactly
✓ end_pos == start_pos + len(original_substring) exactly
✓ replacement_substring != original_substring (different strings)
✓ len(replacement_substring) > 0 and len(original_substring) > 0 (non-empty)
✓ len(replacement_substring) <= len(original_substring) (length constraint)
✓ Perturbation is Tier 1, 2, or 3 (substantive content shift)
✓ target_wrong_answer includes: content shift description, presence markers, absence markers
✓ Replacement changes question focus (not trivial negation)
✓ Replacement is natural and semantically meaningful

## LONG QUESTIONS

{questions_list}

## OUTPUT FORMAT

Return ONLY valid JSON as a single array containing ALL mappings from ALL questions above.
Each question should have {k} mappings.

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
    "target_wrong_answer": "Response focuses on social changes instead of economic metrics. Will contain markers: 'social class', 'living conditions'. Will lack: 'GDP', 'wages'.",
    "reasoning": "...",
    "verification": "'economic impact' → 'social impact' → response discusses sociology → detectable via absent economic terminology"
  }},
  ...
]
```

Return ONLY valid JSON array, no markdown fences, no additional commentary."""


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
- Goal: Generate 3 mappings that cause verifiable deviation from the gold answer (use Tier 1-3 techniques)

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

