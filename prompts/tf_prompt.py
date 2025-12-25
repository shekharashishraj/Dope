"""True/False perturbation prompt template."""
from typing import Dict, Any


TRUE_FALSE_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating text substitutions for True/False questions.

Given:
- LaTeX code for the question stem: {latex_stem_text}
- Gold answer: {gold_answer}
- Question type: {question_type}
- Strategy: replacement
- Reasoning steps:
{reasoning_steps}
- Copyable text (use this exact text when selecting substrings):
<<<COPY
{copyable_text}
>>>
{prefix_note}{answer_guidance}{retry_instructions}

Your task:
Generate {k} valid mappings that satisfy the replacement strategy. Each mapping should:
1. Replace one contiguous substring of the question stem
2. Flip the answer from {gold_answer} to the opposite answer
3. Ensure the replacement is semantically meaningful and natural
4. Cause a verifiable deviation in the answer

### VALIDATION RULES:
- **Zero-Null Constraint**: Neither 'original_substring' nor 'replacement_substring' can be empty or null.
- **Index Math**: start_pos + len(original_substring) MUST exactly equal end_pos.
- **LaTeX Preservation**: The original_substring must be an EXACT literal match of the LaTeX source, including curly braces, backslashes, and commands.
- **Example**: Change "The Earth rotates **eastward**" to "**westward**" (NOT "does not rotate eastward").

### TRUTH-FLIPPING TECHNIQUES:
1. **Comparative Inversion**: Flip "greater than" to "less than" or "increases" to "decreases".
2. **Quantifier Shift**: Change "Always" to "Sometimes" or "All" to "Most".
3. **Property Swap**: Replace a term with its logical opposite (e.g., "Endothermic" to "Exothermic").

### DOMAIN-SPECIFIC FEW-SHOT EXAMPLES:
- **Physics**: 
  *Original*: "Entropy **increases** in an isolated system." (Gold: True)
  *Perturbation*: "Entropy **decreases** in an isolated system." (New: False)
  *Reasoning*: Flipped the directional vector of the second law of thermodynamics.
- **Mathematics**:
  *Original*: "The derivative of $\sin(x)$ is **$\cos(x)$**." (Gold: True)
  *Perturbation*: "The derivative of $\sin(x)$ is **$-\cos(x)$**." (New: False)
  *Reasoning*: Substituted the correct derivative for its negative counterpart.
- **Chemistry**:
  *Original*: "Noble gases have **full** outer shells." (Gold: True)
  *Perturbation*: "Noble gases have **empty** outer shells." (New: False)

### MANDATORY RULES:
- **Zero-Negation Rule**: DO NOT use "not", "is not", "no", or "un-". 
- **Verifiable Factual Flip**: The replacement must make the statement the absolute logical opposite of its original state.
- **Index Math**: start_pos + len(original_substring) MUST exactly equal end_pos.
- **Length Constraint**: len(replacement_substring) <= len(original_substring).

For each mapping, provide:
1. question_index: The question number ({question_index})
2. latex_stem_text: Exact LaTeX text of the question stem (must match the input exactly)
3. original_substring: The substring to replace (must be a contiguous substring of latex_stem_text)
4. replacement_substring: The replacement text
5. start_pos: Start position of original_substring relative to latex_stem_text (0-based index)
6. end_pos: End position of original_substring relative to latex_stem_text (exclusive, 0-based index)
7. target_wrong_answer: The opposite answer (e.g., "False" if gold is "True", or "True" if gold is "False")
8. reasoning: Brief explanation of why this mapping satisfies the strategy

IMPORTANT:
- The original_substring MUST be an exact substring of latex_stem_text
- The start_pos and end_pos MUST be accurate (start_pos + len(original_substring) = end_pos)
- The target_wrong_answer MUST be the opposite of the gold answer
- CRITICAL: The replacement_substring MUST be DIFFERENT from the original_substring. Do NOT generate mappings where original_substring == replacement_substring (e.g., "force" → "force" is INVALID). The replacement MUST change the text to create actual manipulation.
- CRITICAL: Neither original_substring nor replacement_substring can be empty strings. Both must contain actual text.
- LENGTH CONSTRAINT: The replacement_substring MUST be smaller or equal in length to the original_substring (len(replacement_substring) <= len(original_substring)). This is critical for maintaining document layout and preventing text overflow.
- latex_stem_text is provided exactly as it appears in the LaTeX source. Do NOT trim, normalise, or reformat it when determining positions.
- The latex_stem_text may include \item tokens from enumerate environments. Keep the \item token intact and operate on the descriptive text that follows it whenever possible.
- The replacement should be natural and semantically meaningful

Return as JSON array:
[
  {{
    "question_index": {question_index},
    "latex_stem_text": "...",
    "original_substring": "...",
    "replacement_substring": "...",
    "start_pos": 0,
    "end_pos": 5,
    "target_wrong_answer": "False",
    "reasoning": "..."
  }},
  ...
]

Return ONLY valid JSON, no markdown or additional text."""


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
        latex_stem_text: LaTeX code for the question stem
        copyable_text: Plain text version of the question stem
        gold_answer: Correct answer ("True" or "False")
        question_type: Question type (should be "TF")
        question_index: Question number
        k: Number of mappings to generate (default: 3)
        reasoning_steps: LLM thinking/reasoning steps (default: empty)
        prefix_note: Optional prefix note (default: empty)
        answer_guidance: Optional answer guidance (default: empty)
        retry_instructions: Optional retry instructions (default: empty)
    
    Returns:
        Formatted prompt string
    """
    return TRUE_FALSE_REPLACEMENT_PROMPT_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        copyable_text=copyable_text,
        gold_answer=gold_answer,
        question_type=question_type,
        question_index=question_index,
        k=k,
        reasoning_steps=reasoning_steps,
        prefix_note=prefix_note,
        answer_guidance=answer_guidance,
        retry_instructions=retry_instructions
    )

