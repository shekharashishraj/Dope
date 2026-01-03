"""Grouped TF batch prompt v2 - Enhanced with stronger Tier 1 focus and explicit detection warnings."""
from typing import Dict, List, Any


TF_GROUPED_BATCH_TEMPLATE_V2 = """
## SITUATION:
We are creating distractors to be used in True and False questions
to drive LLM away from the correct answer and select the opposite option.

## Role:
You are an expert at generating textual perturbations for True/False questions.

##Task:
Given the questions below, your task is to generate perturbations for each question.

**Strategy:** Replacement (replace exactly ONE contiguous substring in the stem)

Your task:
Generate {k} valid mappings per question that satisfy the replacement strategy. Each mapping should:
1. Replace one contiguous substring of the question stem
2. Flip the answer from the gold answer to the opposite answer
3. Ensure the replacement is semantically meaningful and natural
4. Backed by sustifiable evidence in your response

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
- **Computer Science**:
  *Original*: "A stack follows the Last-In-First-Out (LIFO) principle." (Gold: True)
  *Perturbation*: "A stack follows the **First-In-First-Out (FIFO)** principle." (New: False)
  *Reasoning*: Changed LIFO to FIFO, contradicting stack behavior.
- **Biology**:
  *Original*: "Mitochondria are found only in eukaryotic cells." (Gold: True)
  *Perturbation*: "Mitochondria are found only in **prokaryotic** cells." (New: False)
  *Reasoning*: Prokaryotic cells lack mitochondria, making the statement false.
- **History**:
  *Original*: "The American Revolution began in 1775." (Gold: True)
  *Perturbation*: "The American Revolution began in **1875**." (New: False)
  *Reasoning*: Fighting began in 1775; claiming 1875 is technically incorrect.
- **Economics**:
  *Original*: "When demand increases and supply remains constant, prices typically rise." (Gold: True)
  *Perturbation*: "When demand increases and supply remains constant, prices typically **fall**." (New: False)
  *Reasoning*: Increased demand with constant supply leads to higher prices, not lower.

### MANDATORY RULES:
- **Negation Rule**: Use "not", "is not", "no", or "un-" wherever possible, as these are easy substitutions that can flip the answer from True -> False or vice-versa. 
- **Verifiable Factual Flip**: The replacement must make the statement the absolute logical opposite of its original state.
- **Index Math**: start_pos + len(original_substring) MUST exactly equal end_pos.
- **Length Constraint**: len(replacement_substring) <= len(original_substring).

For each mapping, provide:
1. question_index: The question number
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

## TF QUESTIONS

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
    "target_wrong_answer": "False",
    "reasoning": "..."
  }},
  ...
]
```

Return ONLY valid JSON, no markdown or additional text"""


def format_tf_question_entry_v2(
    question_index: int,
    latex_stem_text: str,
    copyable_text: str,
    gold_answer: str,
    k: int = 3
) -> str:
    """Format a single TF question entry for grouped batch prompt v2."""
    flipped_answer = "False" if gold_answer == "True" else "True"
    return f"""**Question {question_index}:**
- LaTeX stem: `{latex_stem_text}`
- Copyable text: {copyable_text}
- Gold answer: {gold_answer} (MUST flip to {flipped_answer} - use Tier 1 techniques)
- ⚠️ CRITICAL: Your perturbation MUST cause the AI to answer {flipped_answer}. If it's too weak, detection will FAIL.
- Goal: Generate {k} mappings using Tier 1 directional inversions (increases↔decreases, greater↔less, positive↔negative, etc.)

"""


def format_grouped_tf_batch_v2(
    questions: List[Dict[str, Any]],
    k: int = 3
) -> str:
    """
    Format grouped TF batch prompt v2 with enhanced Tier 1 focus.
    
    Args:
        questions: List of question dicts with keys: question_index, latex_stem_text, 
                   copyable_text, gold_answer
        k: Number of mappings per question (default: 3)
    
    Returns:
        Formatted grouped batch prompt v2
    """
    # Determine target answer from first question (all should have same pattern)
    if questions:
        first_gold = questions[0]['gold_answer']
        target_answer = "False" if first_gold == "True" else "True"
    else:
        target_answer = "False"
        first_gold = "True"
    
    questions_list = []
    for q in questions:
        questions_list.append(format_tf_question_entry_v2(
            question_index=q['question_index'],
            latex_stem_text=q['latex_stem_text'],
            copyable_text=q['copyable_text'],
            gold_answer=q['gold_answer'],
            k=k
        ))
    
    total_mappings = len(questions) * k
    
    return TF_GROUPED_BATCH_TEMPLATE_V2.format(
        questions_list="\n".join(questions_list),
        k=k,
        total_mappings=total_mappings,
        gold_answer=first_gold,
        target_answer=target_answer
    )

