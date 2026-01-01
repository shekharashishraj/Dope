"""True/False perturbation prompt template - Improved Version."""
from typing import Dict, Any, List, Optional


TRUE_FALSE_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating text substitutions for True/False questions that reliably flip the truth value.

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

**Example 4 - Flipping False to True:**
```
Statement: "Water boils at 50 degrees Celsius at sea level."
Gold Answer: False
```
```json
{{
  "question_index": 15,
  "latex_stem_text": "Water boils at 50 degrees Celsius at sea level.",
  "original_substring": "50",
  "replacement_substring": "100",
  "start_pos": 15,
  "end_pos": 17,
  "target_wrong_answer": "True",
  "reasoning": "Water boils at 100°C at sea level, not 50°C. Correcting the temperature makes the statement true.",
  "verification": "'50' → '100' → correct boiling point → statement becomes True"
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

**Rejected Example 3 - No factual change (INVALID):**
```
original_substring: "the"
replacement_substring: "a"
```
❌ REJECTED: Does not change the truth value of the statement.

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


# Reasoning steps block template
REASONING_STEPS_BLOCK = """
**LLM Reasoning Context:**
{reasoning_steps}
"""


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


def format_retry_instructions(
    attempt_number: int,
    previous_errors: List[str],
    failed_mappings: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Generate retry instructions based on previous failures.
    
    Args:
        attempt_number: Current attempt number (1-indexed)
        previous_errors: List of error descriptions from previous attempts
        failed_mappings: Optional list of mappings that failed validation
    
    Returns:
        Formatted retry instructions string
    """
    if attempt_number <= 1:
        return ""
    
    instructions = f"""
## ⚠️ RETRY ATTEMPT {attempt_number}

Previous attempt(s) failed validation. Please carefully address these issues:

**Errors to Fix:**
"""
    for i, error in enumerate(previous_errors, 1):
        instructions += f"{i}. {error}\n"
    
    if failed_mappings:
        instructions += "\n**Failed Mappings (DO NOT repeat these patterns):**\n"
        for mapping in failed_mappings[:3]:
            orig = mapping.get('original_substring', 'N/A')
            repl = mapping.get('replacement_substring', 'N/A')
            instructions += f"- '{orig}' → '{repl}' (rejected)\n"
    
    instructions += """
**Recovery Strategy:**
- Use Tier 1 or Tier 2 techniques (directional inversion, property swap)
- Absolutely NO negation words (not, un-, non-, in-, cannot)
- Double-check position calculations using 0-based indexing
- Verify the replacement creates a factually opposite statement
- Confirm replacement length <= original length
"""
    return instructions


# Negation patterns to detect
NEGATION_PATTERNS = [
    "not ", " not", "n't", "cannot", "can not",
    "never", "no ", " no",
    # Prefixes - check if added
]

NEGATION_PREFIXES = ["un", "non", "in", "im", "ir", "il", "dis", "a", "anti"]


def _contains_added_negation(original: str, replacement: str) -> bool:
    """Check if replacement adds negation not present in original."""
    original_lower = original.lower()
    replacement_lower = replacement.lower()
    
    # Check for negation words/patterns
    for pattern in NEGATION_PATTERNS:
        if pattern in replacement_lower and pattern not in original_lower:
            return True
    
    # Check for negation prefixes added
    # This is a heuristic - checks if replacement starts with negation prefix
    # that original doesn't have
    for prefix in NEGATION_PREFIXES:
        if replacement_lower.startswith(prefix) and not original_lower.startswith(prefix):
            # Additional check: the rest should be similar
            if original_lower in replacement_lower[len(prefix):]:
                return True
    
    return False


def validate_mapping(
    mapping: Dict[str, Any],
    latex_stem_text: str,
    gold_answer: str
) -> tuple[bool, List[str]]:
    """
    Validate a single True/False perturbation mapping.
    
    Args:
        mapping: The mapping dictionary to validate
        latex_stem_text: Original LaTeX stem text
        gold_answer: The correct answer ("True" or "False")
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields check
    required_fields = [
        'question_index', 'latex_stem_text', 'original_substring',
        'replacement_substring', 'start_pos', 'end_pos', 'target_wrong_answer'
    ]
    for field in required_fields:
        if field not in mapping:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    original = mapping['original_substring']
    replacement = mapping['replacement_substring']
    start_pos = mapping['start_pos']
    end_pos = mapping['end_pos']
    target = mapping['target_wrong_answer']
    
    # Empty string checks
    if not original:
        errors.append("original_substring cannot be empty")
    if not replacement:
        errors.append("replacement_substring cannot be empty")
    
    # Identity check
    if original == replacement:
        errors.append(f"original_substring equals replacement_substring: '{original}'")
    
    # Length constraint
    if len(replacement) > len(original):
        errors.append(
            f"replacement_substring ({len(replacement)} chars) exceeds "
            f"original_substring ({len(original)} chars)"
        )
    
    # Substring existence check
    if original not in latex_stem_text:
        errors.append(f"original_substring not found in latex_stem_text: '{original}'")
    elif latex_stem_text.count(original) > 1:
        errors.append(f"original_substring appears multiple times: '{original}'")
    
    # Position accuracy check
    if original and original in latex_stem_text:
        actual_start = latex_stem_text.find(original)
        actual_end = actual_start + len(original)
        if start_pos != actual_start:
            errors.append(f"start_pos mismatch: got {start_pos}, expected {actual_start}")
        if end_pos != actual_end:
            errors.append(f"end_pos mismatch: got {end_pos}, expected {actual_end}")
    
    # Position formula check
    if original and start_pos + len(original) != end_pos:
        errors.append(
            f"Position formula violated: start_pos({start_pos}) + "
            f"len('{original}')({len(original)}) != end_pos({end_pos})"
        )
    
    # Target answer check (must be opposite of gold)
    expected_target = "False" if gold_answer.lower() == "true" else "True"
    if target.lower() != expected_target.lower():
        errors.append(
            f"target_wrong_answer ({target}) should be opposite of "
            f"gold_answer ({gold_answer}), expected: {expected_target}"
        )
    
    # Negation check
    if original and replacement and _contains_added_negation(original, replacement):
        errors.append(
            f"Negation detected: '{original}' → '{replacement}' adds negation words/prefixes. "
            f"Use factual inversion instead."
        )
    
    return len(errors) == 0, errors


def get_opposite_answer(answer: str) -> str:
    """Get the opposite True/False answer."""
    return "False" if answer.lower() == "true" else "True"


# Example usage and testing
if __name__ == "__main__":
    # Test case
    prompt = format_tf_prompt(
        latex_stem_text="Entropy increases in an isolated system.",
        copyable_text="Entropy increases in an isolated system.",
        gold_answer="True",
        question_type="TF",
        question_index=3,
        k=3
    )
    
    print("=" * 80)
    print("GENERATED PROMPT:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # Test validation - valid mapping
    valid_mapping = {
        "question_index": 3,
        "latex_stem_text": "Entropy increases in an isolated system.",
        "original_substring": "increases",
        "replacement_substring": "decreases",
        "start_pos": 8,
        "end_pos": 17,
        "target_wrong_answer": "False",
        "reasoning": "Test reasoning",
        "verification": "Test verification"
    }
    
    is_valid, errors = validate_mapping(
        valid_mapping,
        "Entropy increases in an isolated system.",
        "True"
    )
    print(f"\nValid mapping test: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        print("Errors:", errors)
    
    # Test validation - invalid mapping with negation
    invalid_mapping = {
        "question_index": 3,
        "latex_stem_text": "Entropy increases in an isolated system.",
        "original_substring": "increases",
        "replacement_substring": "does not increase",
        "start_pos": 8,
        "end_pos": 17,
        "target_wrong_answer": "False",
        "reasoning": "Test reasoning"
    }
    
    is_valid, errors = validate_mapping(
        invalid_mapping,
        "Entropy increases in an isolated system.",
        "True"
    )
    print(f"\nInvalid mapping test (negation): {'PASS' if not is_valid else 'FAIL'}")
    if errors:
        print("Errors:", errors)