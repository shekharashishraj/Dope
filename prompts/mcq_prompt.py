"""MCQ perturbation prompt template."""
from typing import Dict, Any

# Reasoning steps block template (only included if reasoning_steps provided)
REASONING_STEPS_BLOCK = """
**LLM Reasoning Context:**
{reasoning_steps}
"""


MCQ_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating text substitutions for academic multiple-choice questions that cause predictable answer shifts. Your accuracy is critical.

## INPUT CONTEXT

**LaTeX Source (use for position calculation):**
```
{latex_stem_text}
```

**Plain Text (use for semantic understanding):**
<<<COPY
{copyable_text}
>>>

**Question Metadata:**
- Question Index: {question_index}
- Question Type: {question_type}
- Gold Answer: {gold_answer}

**Answer Options:**
{options}

{reasoning_steps_block}
{prefix_note}{answer_guidance}{retry_instructions}

## TASK

Generate {k} valid perturbation mappings. Each mapping must:
1. Replace ONE contiguous substring in the LaTeX source with a semantically meaningful and natural replacement.
2. Cause the correct answer to shift from {gold_answer} to a specific wrong option (If {gold_answer} is the gold answer, the target wrong answer should be a different option).
3. Preserve grammatical correctness and natural readability
4. Create a semantically coherent (but differently-answered) question

## PERTURBATION QUALITY STANDARDS

**REQUIRED - Hard Constraints:**
- `original_substring` must be an EXACT character-for-character match in `latex_stem_text`
- `replacement_substring` must be DIFFERENT from `original_substring`
- Neither substring can be empty
- Position accuracy: `start_pos + len(original_substring) == end_pos`
- Length constraint: `len(replacement_substring) <= len(original_substring)`

**REQUIRED - Semantic Constraints:**
- Do NOT use trivial negations (adding "not", "never", "don't")
- Do NOT change proper nouns, named entities, or technical terminology to nonsense
- The perturbed question must still be answerable and unambiguous
- The perturbation must create a logical path to `target_wrong_answer`

**QUALITY TIERS (aim for Tier 1):**
- **Tier 1 (Best):** Changes a core entity, parameter, condition, or relationship that fundamentally alters what's being asked.
Example: "maximum" → "minimum", "increases" → "decreases", "before" → "after", "India" → "China"
- **Tier 2 (Acceptable):** Changes scope, quantity, or specificity. 
Example: "all" → "one", "primary" → "secondary", "first" → "last", "global" → "local"
- **Tier 3 (Weak - Avoid):** Surface-level word swaps that don't reliably shift answers.
Example: synonyms, minor qualifiers

## LaTeX HANDLING RULES

- Preserve `\item`, `\begin`, `\end` and structural commands intact
- When perturbing inside math environments (`$...$`, `\[...\]`, `\frac{{}}{{}}`), ensure mathematical validity
- Prefer perturbing descriptive text over LaTeX commands when possible
- If you must modify a command's argument, keep the command structure: `\textbf{{old}}` → `\textbf{{new}}`
- DO NOT edit the options - only edit the stem

## POSITION CALCULATION

Positions are 0-indexed byte offsets relative to `latex_stem_text`:
- `start_pos`: Index of first character of `original_substring`
- `end_pos`: Index immediately AFTER last character (exclusive)
- Verify: `latex_stem_text[start_pos:end_pos] == original_substring`

## EXAMPLES WITH FULL JSON OUTPUT

**Example 1 - Tier 1 (Excellent):**
```
latex_stem_text: "What is the primary function of mitochondria in eukaryotic cells?"
gold_answer: "A" (ATP production)
```
```json
{{
  "question_index": 5,
  "latex_stem_text": "What is the primary function of mitochondria in eukaryotic cells?",
  "original_substring": "primary function",
  "replacement_substring": "least common role",
  "start_pos": 12,
  "end_pos": 28,
  "target_wrong_answer": "C",
  "reasoning": "Changing 'primary function' to 'least common role' inverts the question intent. Mitochondria's least common role among typical options would be C (calcium storage), not A (ATP production).",
  "verification": "'primary function' → 'least common role' → reader seeks rare function → selects C (calcium storage)"
}}
```

**Example 2 - Tier 1 (Excellent):**
```
latex_stem_text: "If interest rates increase, what happens to bond prices?"
gold_answer: "B" (Bond prices decrease)
```
```json
{{
  "question_index": 12,
  "latex_stem_text": "If interest rates increase, what happens to bond prices?",
  "original_substring": "increase",
  "replacement_substring": "decrease",
  "start_pos": 19,
  "end_pos": 27,
  "target_wrong_answer": "A",
  "reasoning": "Inverting the interest rate direction flips the bond price relationship. When rates decrease, bond prices increase (option A).",
  "verification": "'increase' → 'decrease' → inverse rate scenario → selects A (prices increase)"
}}
```

**Rejected Example 1 - Trivial Negation (INVALID):**
```
original_substring: "is"
replacement_substring: "is not"
```
❌ REJECTED: Trivial negation. Unnatural phrasing. Also violates length constraint.

**Rejected Example 2 - No Answer Shift Logic (INVALID):**
```
original_substring: "mitochondria"
replacement_substring: "organelles"
```
❌ REJECTED: Generic substitution doesn't create reliable path to specific wrong answer.

## OUTPUT FORMAT

Return a JSON array with exactly {k} mappings:

```json
[
  {{
    "question_index": {question_index},
    "latex_stem_text": "<exact input latex_stem_text>",
    "original_substring": "<exact substring from latex_stem_text>",
    "replacement_substring": "<replacement text, len <= original>",
    "start_pos": <0-based start index>,
    "end_pos": <0-based exclusive end index>,
    "target_wrong_answer": "<option label, e.g., B, C, or D>",
    "reasoning": "<why this perturbation shifts answer from {gold_answer} to target>",
    "verification": "<causal chain: original → replacement → interpretation → answer selection>"
  }}
]
```

## FINAL CHECKLIST

Before returning, verify each mapping:
☐ `original_substring` appears exactly once in `latex_stem_text`
☐ `start_pos` and `end_pos` are correct (`latex_stem_text[start_pos:end_pos] == original_substring`)
☐ `replacement_substring != original_substring`
☐ `len(replacement_substring) <= len(original_substring)`
☐ `target_wrong_answer != "{gold_answer}"`
☐ Perturbation is Tier 1 or Tier 2 quality
☐ Verification chain logically connects perturbation to answer shift

Return ONLY the JSON array. No markdown fences, no additional commentary."""


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
        latex_stem_text: LaTeX code for the question stem (used for position calculation)
        copyable_text: Plain text version of the question stem (used for semantic understanding)
        gold_answer: Correct answer option (e.g., "A", "B")
        question_type: Question type (should be "MCQ")
        options: Dictionary of options (e.g., {"A": "...", "B": "..."})
        question_index: Question number
        k: Number of mappings to generate (default: 3)
        reasoning_steps: LLM thinking/reasoning steps (default: empty)
        prefix_note: Optional prefix note for special instructions (default: empty)
        answer_guidance: Optional answer guidance (default: empty)
        retry_instructions: Optional retry instructions for failed attempts (default: empty)
    
    Returns:
        Formatted prompt string
    """
    # Format options as a readable string
    options_str = "\n".join([f"  - {key}: {value}" for key, value in options.items()])
    
    # Only include reasoning steps block if provided
    reasoning_steps_block = ""
    if reasoning_steps.strip():
        reasoning_steps_block = REASONING_STEPS_BLOCK.format(reasoning_steps=reasoning_steps)
    
    # Add newlines before optional sections if they have content
    if prefix_note and not prefix_note.startswith("\n"):
        prefix_note = "\n" + prefix_note
    if answer_guidance and not answer_guidance.startswith("\n"):
        answer_guidance = "\n" + answer_guidance
    if retry_instructions and not retry_instructions.startswith("\n"):
        retry_instructions = "\n" + retry_instructions
    
    return MCQ_REPLACEMENT_PROMPT_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        copyable_text=copyable_text,
        gold_answer=gold_answer,
        question_type=question_type,
        options=options_str,
        question_index=question_index,
        k=k,
        reasoning_steps_block=reasoning_steps_block,
        prefix_note=prefix_note,
        answer_guidance=answer_guidance,
        retry_instructions=retry_instructions
    )
