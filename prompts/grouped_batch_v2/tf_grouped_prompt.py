"""Grouped TF batch prompt v2 - Enhanced with stronger Tier 1 focus and explicit detection warnings."""
from typing import Dict, List, Any


TF_GROUPED_BATCH_TEMPLATE_V2 = """
We are creating distractors to be used in True/False questions to drive LLM away from the correct answer.
You are an expert at generating text substitutions for True/False questions that reliably flip the truth value. 

## CRITICAL WARNING

⚠️ **IF YOUR PERTURBATION DOES NOT CLEARLY FLIP THE TRUTH VALUE, IT WILL FAIL DETECTION** ⚠️

The AI model reading the perturbed PDF must answer the OPPOSITE of the gold answer. If the perturbation is too subtle or doesn't change the factual content enough, the AI will still answer the original (gold) answer, and detection will FAIL.

**Success Criteria**: After your replacement, an AI reading the perturbed question MUST answer {target_answer} instead of {gold_answer}. If there's any doubt, the perturbation is TOO WEAK.

## INSTRUCTIONS (apply to ALL questions below)

**Strategy:** Replacement (replace exactly ONE contiguous substring in the stem)

**CRITICAL HARD CONSTRAINTS (must satisfy ALL - verify each mapping):**
1) Single-span edit: replace exactly ONE contiguous substring inside latex_stem_text (stem only, no multiple edits).
   - Full-stem rewrite fallback is allowed: the “one substring” MAY be the ENTIRE stem when a strong short-span Tier 1/2 flip is impossible.
2) Exact match: original_substring MUST be found verbatim in latex_stem_text (character-for-character, including all LaTeX commands, spaces, special characters).
3) Valid indices: latex_stem_text[start_pos:end_pos] == original_substring EXACTLY AND end_pos = start_pos + len(original_substring) EXACTLY.
4) Non-empty strings: Both original_substring and replacement_substring MUST contain actual text (no empty strings, no whitespace-only).
5) Different strings: replacement_substring MUST be different from original_substring (no identical mappings).
6) Length / layout constraint (two modes):
   - Default (short-span preferred): len(replacement_substring) <= len(original_substring); keep replacement similar length (aim: within ±12 characters) and LaTeX well-formed.
   - Full-stem rewrite fallback (entire stem as original_substring): set start_pos=0, end_pos=len(latex_stem_text); keep replacement close in length to the original stem (prefer <=, avoid bloat) and keep LaTeX well-formed.
7) Truth flip: target_wrong_answer MUST be exactly the opposite of gold_answer (if gold is "True", target must be "False", and vice versa).
8) **MANDATORY**: Replacement must make the statement CLEARLY and UNAMBIGUOUSLY switch truth value (not just wording - must be verifiable factual flip that changes the answer).
9) Negation rule: DO NOT rely on inserting/removing "not/never/no". Prefer changing key term, condition, quantifier, number, direction, scope, or entity.
10) Semantic quality: Replacement must be natural and semantically meaningful (not awkward phrasing).
11) **STRENGTH REQUIREMENT**: Use Tier 1 techniques whenever possible. Tier 3-4 techniques often fail detection.

## TRUTH-FLIPPING TECHNIQUES (Ranked by Effectiveness - USE TIER 1)

**Tier 1 - Comparative/Directional Inversion (BEST - Use These First):**
These are the MOST RELIABLE for flipping truth values. Prioritize these patterns:

**Physics/Chemistry:**
- "increases" ↔ "decreases" (e.g., "temperature increases" → "temperature decreases")
- "greater than" ↔ "less than" (e.g., "mass greater than" → "mass less than")
- "positive" ↔ "negative" (e.g., "positive charge" → "negative charge")
- "exothermic" ↔ "endothermic" (e.g., "exothermic reaction" → "endothermic reaction")
- "absorbs" ↔ "releases" (e.g., "absorbs energy" → "releases energy")
- "higher" ↔ "lower" (e.g., "higher pressure" → "lower pressure")
- "clockwise" ↔ "counterclockwise" (e.g., "rotates clockwise" → "rotates counterclockwise")

**Mathematics:**
- "maximum" ↔ "minimum" (e.g., "maximum value" → "minimum value")
- "converges" ↔ "diverges" (e.g., "series converges" → "series diverges")
- "even" ↔ "odd" (e.g., "even number" → "odd number")
- "prime" ↔ "composite" (e.g., "prime number" → "composite number")

**Biology:**
- "dominant" ↔ "recessive" (e.g., "dominant allele" → "recessive allele")
- "active" ↔ "inactive" (e.g., "active site" → "inactive site")
- "aerobic" ↔ "anaerobic" (e.g., "aerobic respiration" → "anaerobic respiration")

**Temporal/Directional:**
- "before" ↔ "after" (e.g., "before the event" → "after the event")
- "increases" ↔ "decreases" (universal)
- "forward" ↔ "backward" (e.g., "forward reaction" → "backward reaction")

**Tier 2 - Property/State Swap (Good, but less reliable than Tier 1):**
- "acidic" ↔ "basic" (e.g., "acidic solution" → "basic solution")
- "conductor" ↔ "insulator" (e.g., "conductor" → "insulator")
- "soluble" ↔ "insoluble" (e.g., "soluble compound" → "insoluble compound")
- "oxidized" ↔ "reduced" (e.g., "oxidized state" → "reduced state")

**Tier 3 - Quantifier Modification (WEAK - Often Fails Detection):**
⚠️ **WARNING**: These often don't flip the answer reliably. Use only if Tier 1-2 are impossible.
- "always" → "sometimes" (True→False)
- "all" → "some" or "most"
- "never" → "rarely"
- "every" → "most"

**Tier 4 - Entity/Value Substitution (WEAKEST - Use as Last Resort):**
⚠️ **WARNING**: These frequently fail. Only use if no Tier 1-2 option exists.
- Swap one correct entity for a related but incorrect one
- Change numerical values to incorrect ones
- Replace correct formula/equation component

## PROHIBITED TECHNIQUES (Will Be Rejected - These Fail Detection)

❌ **Negation insertion**: "is" → "is not", "can" → "cannot", adding "un-", "non-", "in-"
❌ **Double negatives**: Any construction that adds negative particles
❌ **Trivial additions**: "true" → "false", "correct" → "incorrect"
❌ **Identity mappings**: original == replacement
❌ **Weak quantifiers**: "always" → "usually" (too subtle)
❌ **Synonym swaps**: "big" → "large" (doesn't change meaning)

## SUCCESSFUL EXAMPLES (Learn from These)

**Example 1 - Physics (Tier 1 - Excellent):**
```
Original: "The temperature of a gas increases when pressure is constant."
Gold: True
Target: False
Replacement: "increases" → "decreases"
Result: "The temperature of a gas decreases when pressure is constant."
✅ SUCCESS: Clear factual inversion, unambiguous False statement
```

**Example 2 - Chemistry (Tier 1 - Excellent):**
```
Original: "Exothermic reactions release energy."
Gold: True
Target: False
Replacement: "Exothermic" → "Endothermic"
Result: "Endothermic reactions release energy."
✅ SUCCESS: Property swap that clearly flips truth (endothermic absorbs, not releases)
```

**Example 3 - Math (Tier 1 - Excellent):**
```
Original: "The function has a maximum value at x=0."
Gold: True
Target: False
Replacement: "maximum" → "minimum"
Result: "The function has a minimum value at x=0."
✅ SUCCESS: Clear directional inversion
```

**Example 4 - Full-stem rewrite (complete stem substitution - semantically different question):**
```
Original stem (latex_stem_text):
"Mitochondria are the primary site of ATP production in eukaryotic cells."

Gold: True
Target: False

When short-span Tier 1/2 flips are not feasible without ambiguity, you may SUBSTITUTE THE ENTIRE STEM with a completely different statement that is unambiguously {target_answer}.

Strategy: FULL-STEM REWRITE (single-span over entire stem)
original_substring = entire latex_stem_text
start_pos = 0
end_pos = len(latex_stem_text)

replacement_substring (new, semantically different stem):
"Humans have 46 pairs of chromosomes."

✅ SUCCESS: This is a complete stem substitution (entirely different claim) that is unambiguously False (humans have 23 pairs, not 46). No negation is used, the truth value flips reliably, and indices remain deterministic (0 to len). Use this fallback when no clean short-span flip exists.
```

## FAILED EXAMPLES (Avoid These Patterns)

**Example 1 - Too Subtle (Tier 3 - FAILS):**
```
Original: "All mammals are warm-blooded."
Gold: True
Target: False
Replacement: "All" → "Most"
Result: "Most mammals are warm-blooded."
❌ FAILURE: Still factually True, AI will answer True, detection fails
```

**Example 2 - Negation (PROHIBITED - FAILS):**
```
Original: "Water is a compound."
Gold: True
Target: False
Replacement: "is" → "is not"
Result: "Water is not a compound."
❌ FAILURE: Prohibited technique, violates constraints
```

**Example 3 - Full-stem rewrite that FAILS (negation + bloat + ambiguity):**
```
Original stem (latex_stem_text):
"The null hypothesis is rejected when the p-value is greater than the significance level."

Gold: False
Target: True

Bad full-stem rewrite:
"The null hypothesis is not rejected when the p-value is not greater than the significance level, which is generally how hypothesis tests work in many settings."

❌ FAILURE REASONS:
- Uses prohibited negation ("not rejected", "not greater than") instead of a clean directional inversion.
- Bloats the stem with vague commentary ("generally", "many settings") → ambiguity and layout risk.
- "not greater than" weakens the flip (includes equality), so the truth value is not unambiguously flipped.

How to fix (good pattern):
Use a clean factual inversion with full-stem rewrite if needed, e.g. replace the entire stem with:
"The null hypothesis is rejected when the p-value is less than the significance level."
(start_pos=0, end_pos=len(latex_stem_text), replacement keeps length close and flips truth without negation).
```

**Example 4 - Full-stem substitution that FAILS (new statement does not guarantee the target label):**
```
Original stem (latex_stem_text):
"Mitochondria are the primary site of ATP production in eukaryotic cells."

Gold: True
Target: False

Bad full-stem substitution:
"Some mammals lay eggs."

❌ FAILURE REASONS:
- The substitution is semantically different, but it does NOT enforce Target=False.
- The new statement is TRUE (e.g., platypus, echidna), so the model will answer True and detection fails.
- Uses a weak quantifier ("Some") that often preserves truth.

How to fix (good pattern):
Substitute with a statement that is clearly and verifiably False without negation, e.g.:
"Humans have 46 pairs of chromosomes."
(This is unambiguously False - humans have 23 pairs - so the model will answer False and detection succeeds.)
```

## PERTURBATION QUALITY STANDARDS

**REQUIRED - Hard Constraints:**
- `original_substring` must be an EXACT character-for-character match in `latex_stem_text`
- `replacement_substring` must be DIFFERENT from `original_substring`
- Neither substring can be empty
- Position accuracy: `start_pos + len(original_substring) == end_pos`
- Length / layout constraint (two modes):
  - Short-span (preferred): `len(replacement_substring) <= len(original_substring)` and similar length (aim within ±12 characters); keep LaTeX well-formed.
  - Full-stem rewrite fallback (allowed): `original_substring == latex_stem_text`, `start_pos=0`, `end_pos=len(latex_stem_text)`; keep replacement close in length (prefer <=, avoid bloat) and LaTeX well-formed.

**REQUIRED - Semantic Constraints:**
- The perturbed statement must be UNAMBIGUOUSLY {target_answer}
- The perturbation must change factual content, not just add negation
- The result must be a coherent, grammatically correct statement
- **CRITICAL**: After replacement, the statement must be clearly {target_answer} - if there's ambiguity, it's TOO WEAK

**REQUIRED - Strength Constraints:**
- Prefer Tier 1 techniques (directional inversions)
- Avoid Tier 3-4 unless absolutely necessary
- Verify that the replacement creates a clear factual contradiction

**What to output for each mapping:**
- question_index: The question number
- latex_stem_text: Must exactly equal the input latex_stem_text
- original_substring: The substring to replace
- replacement_substring: The replacement text
- start_pos: Start position (0-based)
- end_pos: End position (exclusive)
- target_wrong_answer: "True" or "False" (the flipped label - must be opposite of gold_answer)
- reasoning: 1–2 sentences explaining why the truth value flips after the replacement AND why this perturbation is strong enough to guarantee detection
- verification: Causal chain showing original → replacement → factual change → truth flip → detection success

**VALIDATION CHECKLIST (verify each mapping before including):**
✓ original_substring exists verbatim in latex_stem_text
✓ latex_stem_text[start_pos:end_pos] == original_substring exactly
✓ end_pos == start_pos + len(original_substring) exactly
✓ replacement_substring != original_substring (different strings)
✓ len(replacement_substring) > 0 and len(original_substring) > 0 (non-empty)
✓ Length constraint satisfied:
  - Short-span: len(replacement_substring) <= len(original_substring)
  - Full-stem rewrite (if used): original_substring == latex_stem_text AND start_pos=0 AND end_pos=len(latex_stem_text); replacement kept close in length (prefer <=, avoid bloat)
✓ target_wrong_answer is exactly opposite of gold_answer (True↔False)
✓ NO negation words added ("not", "un-", "non-", "in-", "cannot", etc.)
✓ **Perturbation uses Tier 1 technique (directional inversion, property swap)**
✓ Replacement causes verifiable truth-value flip (not trivial negation)
✓ After replacement, statement is UNAMBIGUOUSLY {target_answer}
✓ Replacement is natural and semantically meaningful
✓ Verification chain shows clear path to detection success

## TF QUESTIONS

{questions_list}

## OUTPUT FORMAT

Return ONLY valid JSON as a single array containing ALL mappings from ALL questions above.
Each question should have {k} mappings.

Total expected mappings: {total_mappings}

```json
[
  {{
    "question_index": 3,
    "latex_stem_text": "...",
    "original_substring": "...",
    "replacement_substring": "...",
    "start_pos": 0,
    "end_pos": 5,
    "target_wrong_answer": "False",
    "reasoning": "Replacing 'increases' with 'decreases' creates a clear factual contradiction. The statement becomes unambiguously False, ensuring the AI will answer False instead of True.",
    "verification": "'increases' → 'decreases' → violates 2nd law of thermodynamics → statement becomes False → AI answers False → detection succeeds"
  }},
  ...
]
```

Return ONLY valid JSON array, no markdown fences, no additional commentary."""


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

