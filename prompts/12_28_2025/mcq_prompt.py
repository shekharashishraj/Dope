"""MCQ perturbation prompt template - Improved Version."""
from typing import Dict, Any, List, Optional


MCQ_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating text substitutions for 
academic multiple-choice questions that cause predictable answer shifts.
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

**Strategy:**
- Replacement

## TASK

Generate {k} valid perturbation mappings. Each mapping must:
1. Replace ONE contiguous substring in the LaTeX source with a semantically meaningful and natural replacement.
2. Cause the correct answer to shift from {gold_answer} to a specific wrong option(If A is the gold answer,
    the target wrong answer should be B, C, or D)
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

## POSITION CALCULATION

Positions are 0-indexed byte offsets relative to `latex_stem_text`:
- `start_pos`: Index of first character of `original_substring`
- `end_pos`: Index immediately AFTER last character (exclusive)
- Verify: `latex_stem_text[start_pos:end_pos] == original_substring`

## EXAMPLES

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

**Example 3 - Rejected (Trivial Negation):**
```
original_substring: "is"
replacement_substring: "is not"
```
❌ REJECTED: Trivial negation. Unnatural phrasing. Also violates length constraint.

**Example 4 - Rejected (No Answer Shift Logic):**
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


# Reasoning steps block template (only included if reasoning_steps provided)
REASONING_STEPS_BLOCK = """
**LLM Reasoning Context:**
{reasoning_steps}
"""


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
        for mapping in failed_mappings[:3]:  # Show at most 3 examples
            orig = mapping.get('original_substring', 'N/A')
            repl = mapping.get('replacement_substring', 'N/A')
            instructions += f"- '{orig}' → '{repl}' (rejected)\n"
    
    instructions += """
**Recovery Strategy:**
- Double-check position calculations using 0-based indexing
- Verify substring exists EXACTLY in latex_stem_text (copy-paste recommended)
- Ensure replacement creates meaningful semantic shift, not just word swap
- Confirm replacement length <= original length
"""
    return instructions


def validate_mapping(
    mapping: Dict[str, Any],
    latex_stem_text: str,
    gold_answer: str
) -> tuple[bool, List[str]]:
    """
    Validate a single perturbation mapping.
    
    Args:
        mapping: The mapping dictionary to validate
        latex_stem_text: Original LaTeX stem text
        gold_answer: The correct answer option
    
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
    if start_pos + len(original) != end_pos:
        errors.append(
            f"Position formula violated: start_pos({start_pos}) + "
            f"len('{original}')({len(original)}) != end_pos({end_pos})"
        )
    
    # Target answer check
    if target == gold_answer:
        errors.append(f"target_wrong_answer ({target}) equals gold_answer ({gold_answer})")
    
    # Trivial negation check
    trivial_negations = ['not ', 'NOT ', "n't", "don't", "doesn't", "isn't", "aren't"]
    for neg in trivial_negations:
        if neg in replacement and neg not in original:
            errors.append(f"Trivial negation detected: '{neg}' added in replacement")
            break
    
    return len(errors) == 0, errors


# Example usage and testing
if __name__ == "__main__":
    # Test case
    test_options = {
        "A": "ATP production through oxidative phosphorylation",
        "B": "Protein synthesis",
        "C": "Calcium ion storage and signaling",
        "D": "DNA replication"
    }
    
    prompt = format_mcq_prompt(
        latex_stem_text="What is the primary function of mitochondria in eukaryotic cells?",
        copyable_text="What is the primary function of mitochondria in eukaryotic cells?",
        gold_answer="A",
        question_type="MCQ",
        options=test_options,
        question_index=5,
        k=3
    )
    
    print("=" * 80)
    print("GENERATED PROMPT:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # Test validation
    test_mapping = {
        "question_index": 5,
        "latex_stem_text": "What is the primary function of mitochondria in eukaryotic cells?",
        "original_substring": "primary function",
        "replacement_substring": "least common role",
        "start_pos": 12,
        "end_pos": 28,
        "target_wrong_answer": "C",
        "reasoning": "Test reasoning",
        "verification": "Test verification"
    }
    
    is_valid, errors = validate_mapping(
        test_mapping,
        "What is the primary function of mitochondria in eukaryotic cells?",
        "A"
    )
    
    print(f"\nValidation result: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        print("Errors:", errors)