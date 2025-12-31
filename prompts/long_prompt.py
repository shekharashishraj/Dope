"""Long-form perturbation prompt template."""
from typing import Dict, Any

# Reasoning steps block template (only included if reasoning_steps provided)
REASONING_STEPS_BLOCK = """
**LLM Reasoning Context:**
{reasoning_steps}
"""


LONG_FORM_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating precise, high-impact text substitutions for long-form questions (essay, short answer, explanation) that cause predictable, detectable deviations in responses. Your accuracy is critical.

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
