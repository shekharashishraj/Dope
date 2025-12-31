"""True/False perturbation prompt template."""
from typing import Dict, Any

# Reasoning steps block template (only included if reasoning_steps provided)
REASONING_STEPS_BLOCK = """
**LLM Reasoning Context:**
{reasoning_steps}
"""


TRUE_FALSE_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating text substitutions for True/False questions that reliably flip the truth value. Your accuracy is critical.

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
- Target Answer: {target_answer}

{reasoning_steps_block}
{prefix_note}{answer_guidance}{retry_instructions}

## TASK

Generate {k} valid perturbation mappings. Each mapping must:
1. Replace ONE contiguous substring in the LaTeX source
2. Flip the truth value from {gold_answer} to {target_answer}
3. Preserve grammatical correctness and natural readability
4. Create a factually opposite statement (not just a negated one)

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

## PERTURBATION QUALITY STANDARDS

**REQUIRED - Hard Constraints:**
- `original_substring` must be an EXACT character-for-character match in `latex_stem_text`
- `replacement_substring` must be DIFFERENT from `original_substring`
- Neither substring can be empty
- Position accuracy: `start_pos + len(original_substring) == end_pos`
- Length constraint: `len(replacement_substring) <= len(original_substring)`

**REQUIRED - Semantic Constraints:**
- The perturbed statement must be unambiguously {target_answer}
- The perturbation must change factual content, not just add negation
- The result must be a coherent, grammatically correct statement

## LaTeX HANDLING RULES

- Preserve `\item`, `\begin`, `\end` and structural commands intact
- When perturbing inside math environments (`$...$`, `\[...\]`), ensure mathematical validity
- For equations, prefer changing values/operators over structural elements
- Keep LaTeX command structure: `\textbf{{old}}` → `\textbf{{new}}`

## POSITION CALCULATION

Positions are 0-indexed byte offsets relative to `latex_stem_text`:
- `start_pos`: Index of first character of `original_substring`
- `end_pos`: Index immediately AFTER last character (exclusive)
- Verify: `latex_stem_text[start_pos:end_pos] == original_substring`

## EXAMPLES WITH FULL JSON OUTPUT

**Example 1 - Tier 1 Directional Inversion (Excellent):**
```
Statement: "Entropy increases in an isolated system."
Gold Answer: True
```
```json
{{
  "question_index": 3,
  "latex_stem_text": "Entropy increases in an isolated system.",
  "original_substring": "increases",
  "replacement_substring": "decreases",
  "start_pos": 8,
  "end_pos": 17,
  "target_wrong_answer": "False",
  "reasoning": "The second law of thermodynamics states entropy increases in isolated systems. Changing to 'decreases' makes this factually false.",
  "verification": "'increases' → 'decreases' → violates 2nd law of thermodynamics → statement becomes False"
}}
```

**Example 2 - Tier 2 Property Swap (Excellent):**
```
Statement: "Noble gases have full outer electron shells."
Gold Answer: True
```
```json
{{
  "question_index": 7,
  "latex_stem_text": "Noble gases have full outer electron shells.",
  "original_substring": "full",
  "replacement_substring": "empty",
  "start_pos": 17,
  "end_pos": 21,
  "target_wrong_answer": "False",
  "reasoning": "Noble gases are characterized by complete valence shells. 'Empty' outer shells would describe highly reactive elements, making the statement false.",
  "verification": "'full' → 'empty' → contradicts noble gas electron configuration → statement becomes False"
}}
```

**Example 3 - Tier 1 with LaTeX Math (Excellent):**
```
Statement: "The derivative of $\sin(x)$ is $\cos(x)$."
Gold Answer: True
```
```json
{{
  "question_index": 12,
  "latex_stem_text": "The derivative of $\\sin(x)$ is $\\cos(x)$.",
  "original_substring": "$\\cos(x)$",
  "replacement_substring": "$-\\sin(x)$",
  "start_pos": 31,
  "end_pos": 40,
  "target_wrong_answer": "False",
  "reasoning": "The derivative of sin(x) is cos(x), not -sin(x). The replacement introduces an incorrect derivative.",
  "verification": "'$\\cos(x)$' → '$-\\sin(x)$' → incorrect calculus identity → statement becomes False"
}}
```

**Rejected Example 1 - Negation (INVALID):**
```
original_substring: "is"
replacement_substring: "is not"
```
❌ REJECTED: Trivial negation. Also violates length constraint.

**Rejected Example 2 - Adding "un-" prefix (INVALID):**
```
original_substring: "stable"
replacement_substring: "unstable"
```
❌ REJECTED: Negation via prefix. Also violates length constraint.

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
    "target_wrong_answer": "{target_answer}",
    "reasoning": "<why this perturbation flips truth value>",
    "verification": "<causal chain: original → replacement → factual change → truth flip>"
  }}
]
```

## FINAL CHECKLIST

Before returning, verify each mapping:
☐ `original_substring` appears exactly once in `latex_stem_text`
☐ `start_pos` and `end_pos` are correct (`latex_stem_text[start_pos:end_pos] == original_substring`)
☐ `replacement_substring != original_substring`
☐ `len(replacement_substring) <= len(original_substring)`
☐ NO negation words added ("not", "un-", "non-", "in-", "cannot", etc.)
☐ Perturbation changes factual content, not just grammatical polarity
☐ Result is unambiguously {target_answer}
☐ Verification chain shows clear factual basis for truth flip

Return ONLY the JSON array. No markdown fences, no additional commentary."""


def format_tf_prompt(
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
    Format True/False replacement prompt with provided parameters.
    
    Args:
        latex_stem_text: LaTeX code for the question stem (used for position calculation)
        copyable_text: Plain text version of the question stem (used for semantic understanding)
        gold_answer: Correct answer ("True" or "False")
        question_type: Question type (should be "TF")
        question_index: Question number
        k: Number of mappings to generate (default: 3)
        reasoning_steps: LLM thinking/reasoning steps (default: empty)
        prefix_note: Optional prefix note for special instructions (default: empty)
        answer_guidance: Optional answer guidance (default: empty)
        retry_instructions: Optional retry instructions for failed attempts (default: empty)
    
    Returns:
        Formatted prompt string
    """
    # Determine target answer (opposite of gold)
    target_answer = "False" if gold_answer.lower() == "true" else "True"
    
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
    
    return TRUE_FALSE_REPLACEMENT_PROMPT_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        copyable_text=copyable_text,
        gold_answer=gold_answer,
        target_answer=target_answer,
        question_type=question_type,
        question_index=question_index,
        k=k,
        reasoning_steps_block=reasoning_steps_block,
        prefix_note=prefix_note,
        answer_guidance=answer_guidance,
        retry_instructions=retry_instructions
    )
