"""Long-form perturbation prompt template - Improved Version."""
from typing import Dict, Any, List, Optional


LONG_FORM_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating text substitutions for long-form questions (essay, short answer, explanation) that cause predictable, detectable deviations in responses.

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

**Expected Answer Focus:**
{gold_answer}

{reasoning_steps_block}
{prefix_note}{answer_guidance}{retry_instructions}

## TASK

Generate {k} valid perturbation mappings. Each mapping must:
1. Replace ONE contiguous substring in the LaTeX source
2. Redirect the question's focus to a DIFFERENT but related concept
3. Create a predictable, detectable deviation pattern in LLM responses
4. Preserve question coherence and answerability

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

## PERTURBATION QUALITY STANDARDS

**REQUIRED - Hard Constraints:**
- `original_substring` must be an EXACT character-for-character match in `latex_stem_text`
- `replacement_substring` must be DIFFERENT from `original_substring`
- Neither substring can be empty
- Position accuracy: `start_pos + len(original_substring) == end_pos`
- Length constraint: `len(replacement_substring) <= len(original_substring)`

**REQUIRED - Semantic Constraints:**
- Perturbed question must still be coherent and answerable
- Deviation must be predictable (you can describe what the wrong answer will contain)
- Change must affect SUBSTANCE, not just style or phrasing
- Result should be a legitimate question (not nonsensical)

**PROHIBITED:**
- Trivial negations ("impact" → "lack of impact")
- Making questions unanswerable or nonsensical
- Changes that don't affect expected answer content
- Overly subtle changes that won't reliably shift responses

## LaTeX HANDLING RULES

- Preserve `\item`, `\begin`, `\end` and structural commands intact
- For questions with multiple parts, target the main question stem
- Keep formatting commands: `\textbf{{old}}` → `\textbf{{new}}`
- Preserve citation/reference structures if present

## POSITION CALCULATION

Positions are 0-indexed byte offsets relative to `latex_stem_text`:
- `start_pos`: Index of first character of `original_substring`
- `end_pos`: Index immediately AFTER last character (exclusive)
- Verify: `latex_stem_text[start_pos:end_pos] == original_substring`

## EXAMPLES WITH FULL JSON OUTPUT

**Example 1 - Tier 1 Scope Shift (Excellent):**
```
Question: "Discuss the economic impact of the Industrial Revolution on European society."
Gold Answer Focus: GDP growth, urbanization economics, wage changes, trade expansion
```
```json
{{
  "question_index": 8,
  "latex_stem_text": "Discuss the economic impact of the Industrial Revolution on European society.",
  "original_substring": "economic impact",
  "replacement_substring": "social impact",
  "start_pos": 12,
  "end_pos": 27,
  "target_wrong_answer": "Response focuses on social changes (class structure, family dynamics, working conditions, urbanization lifestyle) instead of economic metrics. Will contain markers: 'social class', 'living conditions', 'family structure'. Will lack: 'GDP', 'wages', 'trade volume', 'economic growth'.",
  "reasoning": "Shifting from 'economic' to 'social' redirects the entire analytical framework. LLMs will discuss sociology rather than economics, creating clear detection through keyword and concept divergence.",
  "verification": "'economic impact' → 'social impact' → response discusses sociology → detectable via absent economic terminology and present social terminology"
}}
```

**Example 2 - Tier 2 Temporal Shift (Excellent):**
```
Question: "Analyze the causes of inflation in the 21st century global economy."
Gold Answer Focus: QE policies, supply chain disruptions, COVID stimulus, cryptocurrency
```
```json
{{
  "question_index": 14,
  "latex_stem_text": "Analyze the causes of inflation in the 21st century global economy.",
  "original_substring": "21st century",
  "replacement_substring": "20th century",
  "start_pos": 36,
  "end_pos": 48,
  "target_wrong_answer": "Response focuses on historical inflation causes (oil shocks, Bretton Woods collapse, stagflation, Vietnam War spending) instead of modern causes. Will contain markers: 'oil crisis', 'gold standard', 'stagflation', '1970s'. Will lack: 'COVID', 'quantitative easing', 'supply chain', 'cryptocurrency'.",
  "reasoning": "Temporal shift forces discussion of entirely different economic era with different causal factors, easily detectable through historical vs. contemporary terminology.",
  "verification": "'21st century' → '20th century' → historical analysis required → detectable via era-specific economic terminology"
}}
```

**Example 3 - Tier 1 Directional Shift (Excellent):**
```
Question: "Explain the advantages of renewable energy sources over fossil fuels."
Gold Answer Focus: Sustainability, reduced emissions, long-term cost savings, energy independence
```
```json
{{
  "question_index": 22,
  "latex_stem_text": "Explain the advantages of renewable energy sources over fossil fuels.",
  "original_substring": "advantages",
  "replacement_substring": "challenges",
  "start_pos": 12,
  "end_pos": 22,
  "target_wrong_answer": "Response focuses on renewable energy problems (intermittency, storage costs, infrastructure needs, grid integration) instead of benefits. Will contain markers: 'intermittent', 'storage', 'infrastructure cost', 'reliability'. Will lack: 'sustainable', 'clean', 'cost-effective', 'renewable'.",
  "reasoning": "Flipping from 'advantages' to 'challenges' inverts the evaluative direction. LLMs will enumerate problems rather than benefits, creating stark content divergence.",
  "verification": "'advantages' → 'challenges' → critical analysis instead of promotional → detectable via negative vs. positive framing"
}}
```

**Example 4 - Tier 3 Perspective Shift (Good):**
```
Question: "Evaluate the ethics of genetic engineering from a scientific perspective."
Gold Answer Focus: Research methodology, peer review, empirical evidence, scientific consensus
```
```json
{{
  "question_index": 31,
  "latex_stem_text": "Evaluate the ethics of genetic engineering from a scientific perspective.",
  "original_substring": "scientific perspective",
  "replacement_substring": "religious perspective",
  "start_pos": 49,
  "end_pos": 71,
  "target_wrong_answer": "Response focuses on theological concerns (sanctity of life, playing God, natural order, religious doctrine) instead of scientific methodology. Will contain markers: 'sanctity', 'divine', 'natural order', 'moral'. Will lack: 'empirical', 'peer review', 'evidence-based', 'methodology'.",
  "reasoning": "Perspective shift changes the entire evaluative framework from empiricism to theology, producing fundamentally different argumentative structure.",
  "verification": "'scientific perspective' → 'religious perspective' → theological framework → detectable via doctrinal vs. empirical language"
}}
```

**Rejected Example 1 - Trivial Negation (INVALID):**
```
original_substring: "impact"
replacement_substring: "lack of impact"
```
❌ REJECTED: Trivial negation. Also violates length constraint.

**Rejected Example 2 - No Content Shift (INVALID):**
```
original_substring: "Discuss"
replacement_substring: "Explain"
```
❌ REJECTED: Methodological verb change alone doesn't reliably shift answer content.

**Rejected Example 3 - Makes Question Nonsensical (INVALID):**
```
original_substring: "Industrial Revolution"
replacement_substring: "breakfast"
```
❌ REJECTED: Creates incoherent question that can't be meaningfully answered.

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
    "target_wrong_answer": "<detection signature: expected content shift, markers present, markers absent>",
    "reasoning": "<why this perturbation causes detectable deviation>",
    "verification": "<causal chain: original → replacement → content shift → detection method>"
  }}
]
```

## FINAL CHECKLIST

Before returning, verify each mapping:
☐ `original_substring` appears exactly once in `latex_stem_text`
☐ `start_pos` and `end_pos` are correct (`latex_stem_text[start_pos:end_pos] == original_substring`)
☐ `replacement_substring != original_substring`
☐ `len(replacement_substring) <= len(original_substring)`
☐ Perturbation is Tier 1, 2, or 3 (substantive content shift)
☐ `target_wrong_answer` includes: content shift description, presence markers, absence markers
☐ Perturbed question is still coherent and answerable
☐ Verification chain shows clear path from perturbation to detectable deviation

Return ONLY the JSON array. No markdown fences, no additional commentary."""


# Reasoning steps block template
REASONING_STEPS_BLOCK = """
**LLM Reasoning Context:**
{reasoning_steps}
"""


def format_long_prompt(
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
    Format long-form replacement prompt with provided parameters.
    
    Args:
        latex_stem_text: LaTeX code for the question stem (used for position calculation)
        copyable_text: Plain text version of the question stem (used for semantic understanding)
        gold_answer: Expected answer description/key concepts
        question_type: Question type (should be "LONG")
        question_index: Question number
        k: Number of mappings to generate (default: 3)
        reasoning_steps: LLM thinking/reasoning steps (default: empty)
        prefix_note: Optional prefix note for special instructions (default: empty)
        answer_guidance: Optional answer guidance (default: empty)
        retry_instructions: Optional retry instructions for failed attempts (default: empty)
    
    Returns:
        Formatted prompt string
    """
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
    
    return LONG_FORM_REPLACEMENT_PROMPT_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        copyable_text=copyable_text,
        gold_answer=gold_answer,
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
- Use Tier 1-3 techniques (scope shift, temporal shift, perspective shift)
- Ensure target_wrong_answer describes: content shift, presence markers, absence markers
- Double-check position calculations using 0-based indexing
- Verify the perturbed question remains coherent and answerable
- Confirm replacement length <= original length
"""
    return instructions


def validate_mapping(
    mapping: Dict[str, Any],
    latex_stem_text: str
) -> tuple[bool, List[str]]:
    """
    Validate a single long-form perturbation mapping.
    
    Args:
        mapping: The mapping dictionary to validate
        latex_stem_text: Original LaTeX stem text
    
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
    
    # Detection signature quality check
    if target:
        target_lower = target.lower()
        has_content_shift = any(phrase in target_lower for phrase in [
            'focus', 'instead of', 'rather than', 'shift', 'redirect'
        ])
        has_markers = any(phrase in target_lower for phrase in [
            'marker', 'contain', 'will have', 'will include', 'present'
        ])
        has_absence = any(phrase in target_lower for phrase in [
            'lack', 'absent', 'missing', 'without', 'will not contain'
        ])
        
        if not has_content_shift:
            errors.append(
                "target_wrong_answer should describe the content shift "
                "(e.g., 'focuses on X instead of Y')"
            )
        if not has_markers and not has_absence:
            errors.append(
                "target_wrong_answer should include detection markers "
                "(what will be present) or absence markers (what will be missing)"
            )
    
    # Trivial negation check
    trivial_negations = ['lack of', 'absence of', 'no ', 'not ', 'without']
    for neg in trivial_negations:
        if neg in replacement.lower() and neg not in original.lower():
            errors.append(f"Trivial negation detected: '{neg}' added in replacement")
            break
    
    return len(errors) == 0, errors


def extract_detection_components(target_wrong_answer: str) -> Dict[str, Any]:
    """
    Parse target_wrong_answer to extract detection signature components.
    
    Args:
        target_wrong_answer: The detection signature string
    
    Returns:
        Dictionary with 'content_shift', 'presence_markers', 'absence_markers'
    """
    result = {
        'content_shift': None,
        'presence_markers': [],
        'absence_markers': [],
        'raw': target_wrong_answer
    }
    
    # This is a simple heuristic parser - in production you might use
    # more sophisticated NLP or structured output from the LLM
    
    lower = target_wrong_answer.lower()
    
    # Extract content shift (look for "focuses on X instead of Y" patterns)
    if 'instead of' in lower:
        parts = lower.split('instead of')
        if len(parts) >= 2:
            result['content_shift'] = {
                'new_focus': parts[0].strip(),
                'original_focus': parts[1].split('.')[0].strip()
            }
    
    # Extract presence markers (look for quoted terms after "contain" or "markers")
    import re
    presence_pattern = r"(?:contain|marker|include)[^'\"]*['\"]([^'\"]+)['\"]"
    presence_matches = re.findall(presence_pattern, lower)
    result['presence_markers'] = presence_matches
    
    # Extract absence markers (look for quoted terms after "lack" or "absent")
    absence_pattern = r"(?:lack|absent|missing|without)[^'\"]*['\"]([^'\"]+)['\"]"
    absence_matches = re.findall(absence_pattern, lower)
    result['absence_markers'] = absence_matches
    
    return result


# Example usage and testing
if __name__ == "__main__":
    # Test case
    prompt = format_long_prompt(
        latex_stem_text="Discuss the economic impact of the Industrial Revolution on European society.",
        copyable_text="Discuss the economic impact of the Industrial Revolution on European society.",
        gold_answer="GDP growth, urbanization economics, wage changes, trade expansion, manufacturing output",
        question_type="LONG",
        question_index=8,
        k=3
    )
    
    print("=" * 80)
    print("GENERATED PROMPT:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # Test validation - valid mapping
    valid_mapping = {
        "question_index": 8,
        "latex_stem_text": "Discuss the economic impact of the Industrial Revolution on European society.",
        "original_substring": "economic impact",
        "replacement_substring": "social impact",
        "start_pos": 12,
        "end_pos": 27,
        "target_wrong_answer": "Response focuses on social changes instead of economic metrics. Will contain markers: 'social class', 'living conditions'. Will lack: 'GDP', 'wages'.",
        "reasoning": "Test reasoning",
        "verification": "Test verification"
    }
    
    is_valid, errors = validate_mapping(
        valid_mapping,
        "Discuss the economic impact of the Industrial Revolution on European society."
    )
    print(f"\nValid mapping test: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        print("Errors:", errors)
    
    # Test validation - invalid mapping (poor detection signature)
    invalid_mapping = {
        "question_index": 8,
        "latex_stem_text": "Discuss the economic impact of the Industrial Revolution on European society.",
        "original_substring": "economic impact",
        "replacement_substring": "social impact",
        "start_pos": 12,
        "end_pos": 27,
        "target_wrong_answer": "Changes the question topic",  # Too vague
        "reasoning": "Test reasoning"
    }
    
    is_valid, errors = validate_mapping(
        invalid_mapping,
        "Discuss the economic impact of the Industrial Revolution on European society."
    )
    print(f"\nInvalid mapping test (poor signature): {'PASS' if not is_valid else 'FAIL'}")
    if errors:
        print("Errors:", errors)
    
    # Test detection component extraction
    test_signature = "Response focuses on social changes instead of economic metrics. Will contain markers: 'social class', 'living conditions'. Will lack: 'GDP', 'wages'."
    components = extract_detection_components(test_signature)
    print(f"\nExtracted detection components:")
    print(f"  Content shift: {components['content_shift']}")
    print(f"  Presence markers: {components['presence_markers']}")
    print(f"  Absence markers: {components['absence_markers']}")
