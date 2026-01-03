"""Stage 2: Span Selection - Select the exact substring to replace.

This stage focuses on PRECISE SUBSTRING EXTRACTION:
- Identify the exact contiguous span to replace
- Copy it VERBATIM from the stem (character-for-character)

The LLM must quote the substring exactly as it appears.
"""


# =============================================================================
# STAGE 2: SPAN SELECTION TEMPLATE (shared for TF and MCQ)
# =============================================================================

STAGE2_TEMPLATE = """Select the exact substring to replace from the stem.

## STEM
{latex_stem_text}

## FLIP STRATEGY
{flip_strategy}

## CRITICAL RULES
1. **VERBATIM COPY**: Copy the substring EXACTLY as it appears in the stem
   - Character-for-character, including ALL LaTeX commands
   - Include all spaces, punctuation, and special characters
   - Do NOT paraphrase or modify the text

2. **CONTIGUOUS SPAN**: Select a single contiguous piece of text
   - No multiple separate edits
   - The substring must be findable with a simple string search

3. **MINIMAL SPAN**: Select the minimal text needed for the flip
   - Focus on the key term/concept identified in the strategy
   - Include enough context for the replacement to be grammatical

4. **UNIQUE SUBSTRING**: The substring should appear only ONCE in the stem
   - If the term appears multiple times, include more context to make it unique

## EXAMPLES

Good: Copy exactly what appears
- Stem: "The temperature increases when..."
- flip_strategy: "Change 'increases' to 'decreases'"
- original_substring: "increases"  ✅ (exact match)

Bad: Paraphrasing or modification
- original_substring: "Increases"  ❌ (wrong capitalization)
- original_substring: "increase"   ❌ (missing 's')

## OUTPUT FORMAT
Return ONLY valid JSON with no additional text:
{{"original_substring": "exact text copied from stem"}}
"""


def format_stage2_prompt(
    latex_stem_text: str,
    flip_strategy: str,
) -> str:
    """Format Stage 2 prompt for span selection.
    
    Args:
        latex_stem_text: The question stem text
        flip_strategy: The flip strategy from Stage 1
    
    Returns:
        Formatted prompt string
    """
    return STAGE2_TEMPLATE.format(
        latex_stem_text=latex_stem_text,
        flip_strategy=flip_strategy,
    )

