"""Grouped MCQ batch prompt v2 - instructions once, all questions listed together."""
from typing import Dict, List, Any


MCQ_GROUPED_BATCH_TEMPLATE = """
## SITUATION:
We are creating substitue questions by looking at the options of the original question in MCQ questions 
for making more question using same options of the original question.
It's not necessary to change parts of the question/statement only, replacing it entirely
is acceptable given it's answer is being changed towards another option which it must do .

## Role:
You are an expert at generating question substitutions for academic multiple-choice questions 
that cause predictable answer shifts to one of the other 3 options. Let's say the correct answer is A) and the other options are B, C, D.
Your accuracy is critical.
You have to come up with clever and natural question substitutions that are semantically meaningful 
and cause predictable answer shifts to one of the other 3 options (A, B, C, D).

## Task:
You also know the correct answer for each question.
## INSTRUCTIONS (apply to ALL questions below)
**Strategy:** 
1) Replacement of the question with a statement true about one of the other 3 options (replace only the question stem, do not edit the options)
2) It can be ANY semantically meaningful statement true about one of the other 3 options.
3) It should not be in any way related to correct option.
4) It must contradict the selection of correct option. In no case it should be true for the correct option.
5) The number of characters should be less than or equal to the original question stem.

### EXAMPLES:
Original McQ:

What is the capital of France?
Options:
A) Paris
B) London
C) Berlin
D) Rome
Correct Answer: C) Paris
Substitution: Where is the river Thames? Correct Answer: B) London
Here the answer is being changed from C) Paris to B) London.

Above examples have no relation to the original question/statement in any way.
They just need to be semantically meaningful and causing predictable answer shifts to one of the other 3 options (A, B, C, D). That's it.
Original McQ:
Which of the following is not a programming language?
Options:
A) Python
B) Flask
C) C++
D) Java
Correct Answer: Python
Substitution: Which of the following is a compiled programming language? 
Correct Answer: C++
Here the answer is being changed from Flask to C++.

Above examples have no relation to the original question/statement in any way.
They just need to be semantically meaningful and causing predictable answer shifts to one of the other 3 options (A, B, C, D). That's it.
**What to output for each mapping:**
- question_index: The question number
- latex_stem_text: Must exactly equal the input latex_stem_text
- original_substring: The substring to replace
- replacement_substring: The replacement text
- start_pos: Start position (0-based)
- end_pos: End position (exclusive)
- target_wrong_answer: A single option key (e.g., "A", "B", "C", "D") that is NOT the gold answer
- reasoning: 1–2 sentences explaining why the new stem makes target_wrong_answer correct and the gold answer incorrect
- verification: Causal chain showing original → replacement → interpretation → answer selection

**VALIDATION CHECKLIST (verify each mapping before including):**
✓ original_substring exists verbatim in latex_stem_text
✓ latex_stem_text[start_pos:end_pos] == original_substring exactly
✓ end_pos == start_pos + len(original_substring) exactly
✓ replacement_substring != original_substring (different strings)
✓ len(replacement_substring) > 0 and len(original_substring) > 0 (non-empty)
✓ len(replacement_substring) <= len(original_substring) (length constraint)
✓ target_wrong_answer != gold_answer (different option)
✓ Replacement question is Tier 1 or Tier 2 quality

## MCQ QUESTIONS

{questions_list}

## OUTPUT FORMAT

Return ONLY valid JSON as a single array containing ALL mappings from ALL questions above.
Each question should have {k} mappings (one for each other option (A, B, C, D)).

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
    "target_wrong_answer": "B",
    "reasoning": "...",
    "verification": "'primary function' → 'least common role' → reader seeks rare function → selects C"
  }},
  ...
]
```

Return ONLY valid JSON array, no markdown fences, no additional commentary."""


def format_mcq_question_entry(
    question_index: int,
    latex_stem_text: str,
    copyable_text: str,
    gold_answer: str,
    options: Dict[str, str]
) -> str:
    """Format a single MCQ question entry for grouped batch prompt."""
    options_str = "\n".join([f"  - {key}: {value}" for key, value in options.items()])
    return f"""**Question {question_index}:**
- LaTeX stem: `{latex_stem_text}`
- Copyable text: {copyable_text}
- Gold answer: {gold_answer}
- Options:
{options_str}
- Goal: Generate 3 mappings that each make a DIFFERENT option become correct (change answer away from {gold_answer}, use Tier 1-2 techniques)

"""


def format_grouped_mcq_batch(
    questions: List[Dict[str, Any]],
    k: int = 3
) -> str:
    """
    Format grouped MCQ batch prompt.
    
    Args:
        questions: List of question dicts with keys: question_index, latex_stem_text, 
                   copyable_text, gold_answer, options
        k: Number of mappings per question (default: 3)
    
    Returns:
        Formatted grouped batch prompt
    """
    questions_list = []
    for q in questions:
        questions_list.append(format_mcq_question_entry(
            question_index=q['question_index'],
            latex_stem_text=q['latex_stem_text'],
            copyable_text=q['copyable_text'],
            gold_answer=q['gold_answer'],
            options=q['options']
        ))
    
    total_mappings = len(questions) * k
    
    return MCQ_GROUPED_BATCH_TEMPLATE.format(
        questions_list="\n".join(questions_list),
        k=k,
        total_mappings=total_mappings
    )

