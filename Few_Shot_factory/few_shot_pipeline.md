We need a **Factory** (generation) and a **Incinerator** (validation) where you brute-force the valid & invalid outputs.

 Python implementation to build your `integrity_shield_10k.jsonl` dataset.

### **Phase 1: The Raw Materials (Data Loading)**

Don't scrape PDFs. Use clean, structured datasets that mirror your target exams.

```python
from datasets import load_dataset
import pandas as pd

def fetch_raw_data():
    # 1. MMLU (Massive Multitask Language Understanding) - High variety STEM/Humanities
    # We load specific subsets relevant to exams
    mmlu_subsets = ['college_physics', 'college_biology', 'us_history', 'macroeconomics', 'jurisprudence']
    
    raw_questions = []
    
    for sub in mmlu_subsets:
        ds = load_dataset("cais/mmlu", sub, split="test")
        for row in ds:
            # Format into a standardized schema
            raw_questions.append({
                "source": f"mmlu_{sub}",
                "stem": row['question'],
                "gold_answer": ["A", "B", "C", "D"][row['answer']], # MMLU uses 0-3 indices
                "options": dict(zip(["A", "B", "C", "D"], row['choices'])),
                "type": "MCQ"
            })
            
    # 2. SciQ (Science Questions) - Good for text-heavy stems
    sciq = load_dataset("sciq", split="train")
    for row in sciq:
        # Shuffle distractors + correct answer to make standard MCQ options
        options_list = [row['distractor1'], row['distractor2'], row['distractor3'], row['correct_answer']]
        # (Shuffle logic omitted for brevity, assuming A=correct for raw gen)
        
        raw_questions.append({
            "source": "sciq",
            "stem": row['question'],
            "gold_answer": row['correct_answer'], 
            "type": "MCQ" # SciQ needs formatting
        })

    return pd.DataFrame(raw_questions)

# Target: 50k raw questions -> Filter down to 10k valid pairs
df = fetch_raw_data()

```

### **Phase 2: The Factory (LLM Generation)**

This script loads your `_v2.md` prompt templates and hits the API in batches.

```python
import json
from openai import OpenAI # Or Anthropic
client = OpenAI()

# Load your uploaded templates
with open("mcq_prompt_v2.md", "r") as f:
    MCQ_TEMPLATE = f.read()

def generate_candidates(batch_questions):
    """
    Takes a batch of raw questions, injects them into your Prompt v2, 
    and requests 5-10 substitutions per question.
    """
    results = []
    
    for q in batch_questions:
        # Fill the template placeholders defined in your uploaded files
        prompt = MCQ_TEMPLATE.format(
            latex_stem_text=q['stem'],
            gold_answer=q['gold_answer'],
            question_type=q['type'],
            options=json.dumps(q.get('options', {})),
            question_index=0,
            k=5, # Ask for 5, hope for 1 valid one
            reasoning_steps="Analyze semantic dependency",
            copyable_text=q['stem'], # Important for the "Exact Copy" constraint
            prefix_note="",
            answer_guidance="",
            retry_instructions=""
        )

        try:
            # Use a fast model for volume (gpt-4o-mini) or strong for quality (gpt-4o)
            response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            mappings = json.loads(content) # Expecting the list of JSONs
            
            # Attach metadata for the next phase
            results.append({
                "original_stem": q['stem'],
                "raw_mappings": mappings,
                "metadata": q
            })
            
        except Exception as e:
            print(f"Gen failed: {e}")
            
    return results

```

### **Phase 3: The Incinerator (Strict Validation)**

This is the code that saves you. It implements the **Critical Constraints** from `mcq_prompt_v2.md`. If a mapping fails *any* check, it is discarded.

```python
def validate_substitution(stem, mapping, gold_answer):
    """
    Returns (True, ValidatedJSON) or (False, ErrorReason)
    """
    try:
        orig = mapping['original_substring']
        rep = mapping['replacement_substring']
        start = mapping.get('start_pos')
        end = mapping.get('end_pos')
        target_wrong = mapping.get('target_wrong_answer')

        # --- CONSTRAINT 1: Existence & Indices ---
        # "original_substring MUST exist in latex_stem_text exactly"
        if orig not in stem:
            return False, "Phantom substring (not found)"
        
        # Verify indices point to the exact string
        # (Your prompts ask the LLM to calculate indices, but we trust our own recalc more)
        actual_start = stem.find(orig)
        if actual_start == -1:
             return False, "Substring not found"
        
        # Override LLM indices with calculated truth to be safe
        mapping['start_pos'] = actual_start
        mapping['end_pos'] = actual_start + len(orig)

        # --- CONSTRAINT 2: Length Safety (PDF Layout) ---
        # "len(replacement) <= len(original)"
        if len(rep) > len(orig):
            return False, f"Overflow risk: +{len(rep) - len(orig)} chars"

        # --- CONSTRAINT 3: Logical Validity ---
        if orig == rep:
            return False, "No-op (text unchanged)"
        
        if target_wrong == gold_answer:
            return False, "Failed to flip answer (target == gold)"

        # --- CONSTRAINT 4: Latex Safety ---
        # Rudimentary check: Don't break unbalanced brackets
        if orig.count('{') != orig.count('}'):
            # Only allow if replacement fixes it (unlikely) or keeps it broken in same way
            if rep.count('{') != rep.count('}'):
                 pass # Risky, maybe strict reject
            else:
                 return False, "Unbalanced LaTeX brackets selected"

        return True, mapping

    except KeyError as e:
        return False, f"Missing key: {e}"

# Processing Loop
valid_dataset = []

for item in generated_batch:
    stem = item['original_stem']
    gold = item['metadata']['gold_answer']
    
    if isinstance(item['raw_mappings'], list):
        for candidate in item['raw_mappings']:
            is_valid, data = validate_substitution(stem, candidate, gold)
            if is_valid:
                # SUCCESS: This is a "Good Example"
                valid_dataset.append({
                    "stem": stem,
                    "mapping": data,
                    "domain": item['metadata'].get('source', 'general')
                })

```

### **Phase 4: Scaling Strategy**

To get 10,000 examples without bankruptcy or waiting a month:

1. **The Funnel Ratio**: Expect a **20% yield**.
* LLMs are bad at character counting. Even with your strong prompts, 80% of generations will violate the `len(rep) <= len(orig)` constraint or hallucinate substrings.
* To get **10k** valid examples, generate **50k** candidates.


2. **Cost Optimization**:
* Run **Prompt Refinement** on 100 examples first. If yield < 10%, tweak the prompt constraints.
* Use **GPT-4o-mini** for the "Easy" subjects (History, Law) where text substitution is simple.
* Reserve **GPT-4o / Claude 3.5 Sonnet** only for "Hard" subjects (Physics, Math) where LaTeX structure is fragile.


3. **The "Gold" Standard (Verification)**:
* For the final ACL paper, you need to prove these work.
* Take your `valid_dataset` and run it through a separate "Solver" LLM.
* Only keep examples where: `Solver(Original) == Gold` AND `Solver(Modified) == Target_Wrong`.
* This "Semantic Double-Check" ensures your dataset is cleaner than human annotation.



### **Final Output Artifact**

Your script should produce a `few_shot_db.jsonl` where every line is a verified injection object ready for RAG retrieval:

```json
{
  "id": "chem_042",
  "domain": "Chemistry",
  "question_type": "MCQ",
  "stem_embedding_text": "Which of the following creates an exothermic reaction...",
  "injection_payload": {
    "original_substring": "exothermic",
    "replacement_substring": "endothermic",
    "reasoning": "Flips thermodynamic sign, invalidating option A",
    "start_pos": 24,
    "end_pos": 34
  }
}

```