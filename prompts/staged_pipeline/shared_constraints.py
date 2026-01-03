"""Shared constraints extracted from existing TF and MCQ templates.

These constraints are reused across all stages of the staged pipeline to ensure
consistency with the original grouped batch prompts.
"""

# =============================================================================
# TF TIER GUIDANCE (from tf_grouped_prompt.py lines 37-85)
# =============================================================================

TF_TIER_GUIDANCE = """
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
"""

# =============================================================================
# TF PROHIBITED TECHNIQUES (from tf_grouped_prompt.py lines 86-94)
# =============================================================================

TF_PROHIBITED_TECHNIQUES = """
## PROHIBITED TECHNIQUES (Will Be Rejected - These Fail Detection)

❌ **Negation insertion**: "is" → "is not", "can" → "cannot", adding "un-", "non-", "in-"
❌ **Double negatives**: Any construction that adds negative particles
❌ **Trivial additions**: "true" → "false", "correct" → "incorrect"
❌ **Identity mappings**: original == replacement
❌ **Weak quantifiers**: "always" → "usually" (too subtle)
❌ **Synonym swaps**: "big" → "large" (doesn't change meaning)
"""

# =============================================================================
# MCQ TIER GUIDANCE (from mcq_grouped_prompt.py lines 25-50)
# =============================================================================

MCQ_TIER_GUIDANCE = """
## QUALITY TIERS (aim for Tier 1)

**Tier 1 (Best):** 
1. Intelligently changes the question to be consistent towards one of the wrong options. 
Take the option that is most likely to be correct and change the question to be consistent towards it.
Do not change the question to be consistent towards the gold answer.

Few Shot Examples: 
Q)  "What is the capital of France?"(Correct Options:
    A) Paris, B) London, C) Berlin, D) Rome) , Correct Answer: A) Paris
    -> "What is the capital of Germany?"(Correct Options:
        A) Paris, B) London, C) Berlin, D) Rome),
        Target Wrong Answer: C) Berlin

Q) Adding more basis functions in a linear model, pick the most probably option:(Correct Options: 
    A) Decreases model bias, B) Increases estimation bias, C) Doesn't affect bias and variance,
    D) Increases both bias and variance, E) Decreases variance), Correct Answer: A) Decreases model bias
-> "Removing basis functions in a linear model, pick the most probably option:"(Correct Options: 
    A) Decreases model bias, B) Increases estimation bias, C) Doesn't affect bias and variance,
    D) Increases both bias and variance, E) Decreases variance), 
    Target Wrong Answer: E) Decreases Variance

2. Changes a core entity, parameter, condition, or relationship that fundamentally alters what's being asked.
Example: "maximum" → "minimum", "increases" → "decreases", "before" → "after", "India" → "China"

3. Changes the scope, quantity, or specificity of the question so that one of the wrong options becomes the correct answer.
Example: "all" → "one", "primary" → "secondary", "first" → "last", "global" → "local"
"""

# =============================================================================
# NEGATION RULE (shared between TF and MCQ)
# =============================================================================

NEGATION_RULE = """
**Negation Rule:** DO NOT rely on inserting/removing "not/never/no". 
Prefer changing key term, condition, quantifier, number, direction, scope, or entity.

PROHIBITED patterns:
- "is" → "is not"
- "can" → "cannot"  
- Adding prefixes: "un-", "non-", "in-", "im-"
- "true" → "false", "correct" → "incorrect"
"""

# =============================================================================
# LENGTH CONSTRAINTS
# =============================================================================

LENGTH_CONSTRAINT_MCQ = """
**Length Constraint (MANDATORY for MCQ):**
- len(replacement_substring) <= len(original_substring)
- This prevents layout issues during PDF rendering
- Aim for similar length (within ±12 characters)
"""

LENGTH_CONSTRAINT_TF = """
**Length Constraint (TF - Flexible):**
- Short-span preferred: len(replacement_substring) <= len(original_substring)
- Keep replacement similar length (aim within ±12 characters)
- Full-stem rewrite fallback is allowed when short-span flip is impossible:
  - original_substring = entire stem
  - Keep replacement close in length (prefer <=, avoid bloat)
"""

# =============================================================================
# LATEX RULE
# =============================================================================

LATEX_RULE = """
**LaTeX Rule:**
- Keep LaTeX well-formed after replacement
- Preserve LaTeX commands, braces, and special characters
- Ensure the result renders correctly
"""

# =============================================================================
# SUCCESSFUL EXAMPLES (for reference in prompts)
# =============================================================================

TF_SUCCESSFUL_EXAMPLES = """
## SUCCESSFUL EXAMPLES

**Example 1 - Physics (Tier 1 - Excellent):**
Original: "The temperature of a gas increases when pressure is constant."
Gold: True, Target: False
Replacement: "increases" → "decreases"
Result: "The temperature of a gas decreases when pressure is constant."
✅ SUCCESS: Clear factual inversion, unambiguous False statement

**Example 2 - Chemistry (Tier 1 - Excellent):**
Original: "Exothermic reactions release energy."
Gold: True, Target: False
Replacement: "Exothermic" → "Endothermic"
Result: "Endothermic reactions release energy."
✅ SUCCESS: Property swap that clearly flips truth

**Example 3 - Math (Tier 1 - Excellent):**
Original: "The function has a maximum value at x=0."
Gold: True, Target: False
Replacement: "maximum" → "minimum"
Result: "The function has a minimum value at x=0."
✅ SUCCESS: Clear directional inversion
"""

TF_FAILED_EXAMPLES = """
## FAILED EXAMPLES (Avoid These Patterns)

**Example 1 - Too Subtle (Tier 3 - FAILS):**
Original: "All mammals are warm-blooded."
Replacement: "All" → "Most"
Result: "Most mammals are warm-blooded."
❌ FAILURE: Still factually True, detection fails

**Example 2 - Negation (PROHIBITED - FAILS):**
Original: "Water is a compound."
Replacement: "is" → "is not"
Result: "Water is not a compound."
❌ FAILURE: Prohibited technique
"""

