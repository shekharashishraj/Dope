# Prompt Template Structure Documentation

## Overview

This document describes the structure of grouped batch prompts, specifically how the v3 templates are organized to work with batch processing while maintaining the original content structure.

## Template Architecture

### Grouped Batch Structure

Grouped batch prompts are designed to process multiple questions in a single API call. The structure separates:

1. **Shared Instructions** - Apply to all questions
2. **Individual Questions** - Formatted separately and inserted into template
3. **Output Format** - Instructions for the combined response

### Key Principle

**Single-question placeholders** (like `{latex_stem_text}`, `{gold_answer}`) are removed from the main template because:
- Each question has different values
- They are formatted individually and included in `{questions_list}`
- The main template only needs shared placeholders

## Template Components

### Main Template Placeholders

The main template (`TF_GROUPED_BATCH_TEMPLATE_V2`) only contains:

- `{questions_list}` - List of formatted individual questions
- `{k}` - Number of mappings per question
- `{total_mappings}` - Total expected mappings (len(questions) * k)
- `{target_answer}` - Target wrong answer (opposite of gold)
- `{gold_answer}` - Gold answer from first question (for reference)

### Individual Question Formatting

Individual questions are formatted by `format_tf_question_entry_v2()`:

```python
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
```

## Template Structure Comparison

### v2 Structure (Reference)

```
## CRITICAL WARNING
[Warning about detection failure]

## INSTRUCTIONS (apply to ALL questions below)
[General instructions]

## TRUTH-FLIPPING TECHNIQUES
[Techniques with tiers]

## TF QUESTIONS

{questions_list}  # Individual questions here

## OUTPUT FORMAT
[Format instructions]
```

### v3 Structure (Current)

```
## SITUATION:
[General situation]

## Role:
[Role description]

##Task:
[General task instructions]

### VALIDATION RULES:
[Rules]

### TRUTH-FLIPPING TECHNIQUES:
[Techniques]

### DOMAIN-SPECIFIC FEW-SHOT EXAMPLES:
[Examples]

### MANDATORY RULES:
[Rules]

## TF QUESTIONS

{questions_list}  # Individual questions here

## OUTPUT FORMAT
[Format instructions]
```

## How It Works

### Batch Generation Flow

1. **Question Grouping** (`src/openai_client.py`):
   ```python
   # Group questions by type
   questions_by_type = defaultdict(list)
   for idx in question_indices:
       meta = question_metadata[idx]
       q_type = meta.get('question_type', 'MCQ').upper()
       questions_by_type[q_type].append({
           'question_index': idx,
           'latex_stem_text': meta.get('latex_stem_text', ''),
           'copyable_text': meta.get('copyable_text', ''),
           'gold_answer': meta.get('gold_answer', ''),
           'options': meta.get('options', {})
       })
   ```

2. **Template Formatting**:
   ```python
   # For TF questions
   section = format_grouped_tf_batch(type_questions, k=self.mappings_per_question)
   ```

3. **Individual Question Formatting**:
   ```python
   for q in questions:
       questions_list.append(format_tf_question_entry_v2(
           question_index=q['question_index'],
           latex_stem_text=q['latex_stem_text'],
           copyable_text=q['copyable_text'],
           gold_answer=q['gold_answer'],
           k=k
       ))
   ```

4. **Template Assembly**:
   ```python
   return TF_GROUPED_BATCH_TEMPLATE_V2.format(
       questions_list="\n".join(questions_list),
       k=k,
       total_mappings=total_mappings,
       gold_answer=first_gold,
       target_answer=target_answer
   )
   ```

## Example Output

### Generated Prompt Structure

```
## SITUATION:
We are creating distractors to be used in True and False questions
to drive LLM away from the correct answer and select the opposite option.

## Role:
You are an expert at generating textual perturbations for True/False questions.

##Task:
Given the questions below, your task is to generate perturbations for each question.

[... instructions ...]

## TF QUESTIONS

**Question 1:**
- LaTeX stem: `The correct answer to 'What is...' is 'True'.`
- Copyable text: The correct answer to 'What is...' is 'True'.
- Gold answer: True (MUST flip to False - use Tier 1 techniques)
- ⚠️ CRITICAL: Your perturbation MUST cause the AI to answer False. If it's too weak, detection will FAIL.
- Goal: Generate 3 mappings using Tier 1 directional inversions (increases↔decreases, greater↔less, positive↔negative, etc.)

**Question 2:**
- LaTeX stem: `The correct answer to 'Which of...' is 'False'.`
- Copyable text: The correct answer to 'Which of...' is 'False'.
- Gold answer: False (MUST flip to True - use Tier 1 techniques)
- ⚠️ CRITICAL: Your perturbation MUST cause the AI to answer True. If it's too weak, detection will FAIL.
- Goal: Generate 3 mappings using Tier 1 directional inversions (increases↔decreases, greater↔less, positive↔negative, etc.)

[... more questions ...]

## OUTPUT FORMAT

Return ONLY valid JSON as a single array containing ALL mappings from ALL questions above.
Each question should have 3 mappings.

Total expected mappings: 36

[... format example ...]
```

## Key Differences: v2 vs v3

### v2 Template
- More detailed with tier-based techniques
- Extensive examples and warnings
- Focus on detection success
- Prohibited techniques list

### v3 Template
- Simpler, cleaner structure
- Original content preserved
- Domain-specific examples
- Focus on validation rules

### Common Structure
- Both use `{questions_list}` for individual questions
- Both use `{k}` and `{total_mappings}` for output format
- Both format individual questions separately

## Best Practices

### Template Design

1. **Keep shared instructions general** - They apply to all questions
2. **Use `{questions_list}` for individual data** - Each question has unique values
3. **Avoid single-question placeholders in main template** - They won't work with batches
4. **Format individual questions clearly** - Use consistent formatting in `format_*_question_entry_*()`

### Question Formatting

1. **Include all necessary data** - LaTeX stem, copyable text, gold answer
2. **Make instructions clear** - Each question should be self-contained
3. **Use consistent structure** - Helps model parse and respond correctly

## Troubleshooting

### Issue: KeyError for placeholder

**Cause**: Template has placeholder that's not provided in `format()` call

**Solution**: 
- Remove single-question placeholders from main template
- Include them in individual question formatting instead

### Issue: Questions not formatted correctly

**Cause**: `format_*_question_entry_*()` not called or incorrect parameters

**Solution**: 
- Check that all required parameters are passed
- Verify question metadata has all required fields

### Issue: Template too long

**Cause**: Too many questions or too verbose instructions

**Solution**:
- Reduce number of questions per batch
- Simplify instructions
- Use shorter examples

## File Locations

- **TF Template**: `prompts/grouped_batch_v3/tf_grouped_prompt.py`
- **MCQ Template**: `prompts/grouped_batch_v3/mcq_grouped_prompt.py`
- **Long Template**: `prompts/grouped_batch_v3/long_grouped_prompt.py`
- **Usage**: `src/openai_client.py` - `batch_generate_perturbations()`

## References

- Grouped Batch v2: `prompts/grouped_batch_v2/tf_grouped_prompt.py`
- OpenAI Batch API: https://platform.openai.com/docs/guides/batch

