SYSTEM_PROMPT="""

You are an expert at generating text substitutions for parts of long-form questions  that makes the answer 
deviate from the gold answer.This is for shielding a question paper so that a student can not cheat by uploading it to a chatbot.
"""
PROMPT="""
You are an expert at generating text substitutions for parts of long-form questions (essay, short answer, etc.) 
that deviate from the gold answer. You will be given a question stem and a gold answer.
You will need to generate a text substitution that deviates from the gold answer.
You will need to generate a text substitution that is semantically meaningful and natural.
You will need to generate a text substitution that is verifiable and detectable.


Given:
- LaTeX code for the question stem: {latex_stem_text}
- Gold answer: {gold_answer}
- Question type: {question_type}
- Strategy: replacement
- Reasoning steps:
{reasoning_steps}
"""