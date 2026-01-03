"""Grouped TF batch prompt v2 - Enhanced with stronger Tier 1 focus and explicit detection warnings."""
from typing import Dict, List, Any


TF_GROUPED_BATCH_TEMPLATE_V2 = """
## SITUATION:
We are substituting question/statements in True and False questions
to make the LLM answer the opposite option(False if True, True if False). Your accuracy is critical.

##Task:
Given the questions below, your task is to generate question substitutions for each question.
Replacing the question stem entirely is acceptable given it's truth value is being changed. 
They don't need to be related to the original question/statement in any way. 
They just need to be semantically meaningful and of opposite truth value. That's it. 

**Strategy:** 
1) Semantic Substitution : substitute the question stem with a semantically meaningful
and natural substitution.
2) Negation (negate the question stem). 

### EXAMPLES:(No need to use these examples, just understand the concept)

Original: The color of leaves is green
Substitution: The capital of Spain is Milan.
Here the truth value is being changed from True to False.

Original: C++ is a programming language.
Substitution: Newton won Nobel Prize.
Here the truth value is being changed from True to False.

Original: The Earth is a planet.
Substitution: Moon is a star.
Here the truth value is being changed from True to False.

Above examples have no relation to the original question/statement in any way.
They just need to be semantically meaningful and of opposite truth value. That's it.
This is very important.

##Bad Examples:
{{
          "question_index": 3,
          "latex_stem_text": "The correct answer to 'What is the dimensionality of the null space of the following matrix? A = [[3, 2, -9], [-6, -4, 18], [12, 8, -36]]' is '2'.",
          "original_substring": "The correct answer to 'What is the dimensionality of the null space of the following matrix? A = [[3, 2, -9], [-6, -4, 18], [12, 8, -36]]' is '2'.",
          "replacement_substring": "The correct answer to 'The capital city of France is Paris.' is '2'.",
          "start_pos": 0,
          "end_pos": 155,
          "target_wrong_answer": "False",
          "reasoning": "The statement "The capital city of France is Paris" is true, so saying the correct answer is '2' is false, flipping the truth value from the original true statement. This is a clear semantic substitution with opposite factual value.",
          }}
        }}
        This is such a bad example, what does this even mean? "The captial city of france is paris" is true, so saying the correct answer is '2' is crap,
        it doesn't make any sense.LLM will answer true anyway. 
        Instead something like "The captial city of france is not paris" would be a good substitution. 
        remove the is 2 part why is that even needed !
        So a good replacement_substring should be something like "The captial city of france is not paris" or "AI stands for Artificial infoknowledge" or "The captial city of france is delhi"
}}

"original_substring": "A normal resting heart rate for an adult is considered to be between 70 and 90 beats per minute.",
"replacement_substring": "A normal resting heart rate for an adult is often considered to be between 60 and 100 beats per minute.",
Why can't we just use "Heart pumps blood?" -> Simple , from the same domain, yet effective.

Your task:
Generate {k} valid question substitutions per question that satisfy the replacement strategy. Each question substitution should:
1. Replace the question stem with a semantically meaningful and natural substitution.
2. The number of characters should be less than or equal to the original question stem. Very Important.
3. It can be ANY semantically meaningful and of opposite truth value statement.

### MANDATORY RULES: 
- **Verifiable Factual Flip**: The question substitution must make the statement the absolute logical opposite of its original state.
- **Semantic Substitution**: The question substitution must be semantically meaningful and natural.

For each question substitution, provide:
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
- The substitution should be natural and semantically meaningful

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
- Gold answer: {gold_answer} (MUST flip to {flipped_answer} - use Semantic Substitution)
- ⚠️ CRITICAL: Your substitution MUST cause the AI to answer {flipped_answer}. If it's too weak, detection will FAIL.
- Goal: Generate {k} substitutions using Semantic Substitution
"""


def format_grouped_tf_batch_v2(
    questions: List[Dict[str, Any]],
    k: int = 3
) -> str:
    """
    Format grouped TF batch prompt v2 with Semantic Substitution.
    
    Args:
        questions: List of question dicts with keys: question_index, latex_stem_text, 
                   copyable_text, gold_answer
        k: Number of substitutions per question (default: 3)
    
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

