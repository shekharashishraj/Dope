"""MCQ perturbation prompt template."""
from typing import Dict, Any


MCQ_REPLACEMENT_PROMPT_TEMPLATE = """You are an expert at generating text substitutions for academic multiple-choice questions displayed on webpages.

Given:
- Question text (extracted from HTML): {question_text}
- Gold answer: {gold_answer}
- Options: {options}

IMPORTANT: The question text is extracted from the rendered HTML. Calculate start_pos and end_pos relative to this exact HTML-extracted text.

STRATEGY: Target-First, Option-Grounded Perturbation

Step 1: Choose target_wrong_answer FIRST
- Pick a wrong option label (different from {gold_answer})
- Copy the option text for that label
- Identify key phrases/keywords from that option

Step 2: Edit the stem to align with the chosen wrong option
- Make the edited question unambiguously match that option's wording
- Use key phrases from the chosen wrong option in your replacement
- The replacement should make the best answer become the target_wrong_answer

Step 3: Prefer short semantic flips (to satisfy length constraint)
- Negation swaps: "always" → "never", "all" → "none"
- Key term swaps: "repeating dependencies" → "partial dependencies"
- Scope swaps: "highest" → "lowest", "maximum" → "minimum"
- Qualifier swaps: "outside the nucleus" → "inside the nucleus"
- Edit ONE hinge phrase only when possible

Your task:
Generate {k} valid mappings that satisfy the replacement strategy. Each mapping should:
1. Replace one contiguous substring of the question text
2. Change the answer from the gold option ({gold_answer}) to a different incorrect option
3. Ensure the replacement is semantically meaningful and natural
4. Cause a verifiable deviation in the answer

For each mapping, provide:
1. question_index: The question number ({question_index})
2. original_substring: The substring to replace (must be a contiguous substring of the question text)
3. replacement_substring: The replacement text
4. start_pos: Start position of original_substring relative to question text (0-based index)
5. end_pos: End position of original_substring relative to question text (exclusive, 0-based index)
6. left_context: Up to 15 characters immediately before the substring (for disambiguation)
7. right_context: Up to 15 characters immediately after the substring (for disambiguation)
8. target_wrong_answer: The target incorrect option label (e.g., "B", "C", "D")
9. after_best_answer: The answer after perturbation (MUST equal target_wrong_answer)
10. supporting_keywords: List of 2-5 key words/phrases from the target option that justify this mapping
11. reasoning: Brief explanation that MUST reference keywords from the chosen wrong option and explain why the edited question matches that option

IMPORTANT:
- The original_substring MUST be an exact substring of the question text
- The start_pos and end_pos MUST be accurate (start_pos + len(original_substring) = end_pos)
- The target_wrong_answer MUST be different from the gold answer
- CRITICAL: Choose target_wrong_answer FIRST, then edit the stem so the best answer becomes that option
- CRITICAL: The replacement_substring MUST be DIFFERENT from the original_substring. Do NOT generate mappings where original_substring == replacement_substring.
- CRITICAL: Neither original_substring nor replacement_substring can be empty strings. Both must contain actual text.
- LENGTH CONSTRAINT: The replacement_substring MUST be smaller or equal in length to the original_substring (len(replacement_substring) <= len(original_substring)). Prefer short semantic flips to satisfy this.
- VERIFICATION: after_best_answer MUST equal target_wrong_answer. This verifies the perturbation actually changes the answer.
- The question text is extracted from HTML and provided exactly as it appears. Do NOT trim, normalise, or reformat it when determining positions.
- The question text may contain newline characters (\\n) or whitespace from HTML formatting. Use the exact text as provided when calculating positions.
- CRITICAL: Calculate positions based on this HTML-extracted text, as it will be used for applying the perturbation to the HTML.
- The replacement should be natural and semantically meaningful

Return as JSON object with a "mappings" key containing the array:
{{
  "mappings": [
    {{
      "question_index": {question_index},
      "original_substring": "...",
      "replacement_substring": "...",
      "start_pos": 0,
      "end_pos": 5,
      "left_context": "...",
      "right_context": "...",
      "target_wrong_answer": "B",
      "after_best_answer": "B",
      "supporting_keywords": ["keyword1", "keyword2"],
      "reasoning": "..."
    }},
    ...
  ]
}}

Return ONLY valid JSON, no markdown or additional text."""


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
        latex_stem_text: Question text (parameter name kept for compatibility with calling code)
        copyable_text: Question text (same as latex_stem_text, kept for compatibility)
        gold_answer: Correct answer option (e.g., "A", "B")
        question_type: Question type (should be "MCQ")
        options: Dictionary of options (e.g., {"A": "...", "B": "..."})
        question_index: Question number
        k: Number of mappings to generate (default: 3)
        reasoning_steps: Not used (kept for compatibility)
        prefix_note: Not used (kept for compatibility)
        answer_guidance: Not used (kept for compatibility)
        retry_instructions: Not used (kept for compatibility)
    
    Returns:
        Formatted prompt string
    """
    # Format options as a readable string
    options_str = "\n".join([f"{key}: {value}" for key, value in options.items()])
    
    return MCQ_REPLACEMENT_PROMPT_TEMPLATE.format(
        question_text=latex_stem_text,  # Use question_text in prompt, but parameter name stays for compatibility
        gold_answer=gold_answer,
        options=options_str,
        question_index=question_index,
        k=k
    )
