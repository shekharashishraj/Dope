#!/usr/bin/env python3
"""
Generate human-authored answer files from detection results.
Creates .txt files similar to answer_key_answerkey.pdf format.
"""

import json
import re
import random
from pathlib import Path
from typing import Dict, List, Tuple
import random

# Grammatical errors to introduce
GRAMMATICAL_ERRORS = [
    ("the", "teh"),
    ("is", "are"),
    ("are", "is"),
    ("was", "were"),
    ("were", "was"),
    ("has", "have"),
    ("have", "has"),
    ("does", "do"),
    ("do", "does"),
    ("its", "it's"),
    ("it's", "its"),
    ("their", "there"),
    ("there", "their"),
    ("they're", "their"),
    ("you're", "your"),
    ("your", "you're"),
    ("affect", "effect"),
    ("effect", "affect"),
    ("principle", "principal"),
    ("principal", "principle"),
    ("complement", "compliment"),
    ("compliment", "complement"),
    ("stationary", "stationery"),
    ("stationery", "stationary"),
    ("loose", "lose"),
    ("lose", "loose"),
    ("accept", "except"),
    ("except", "accept"),
    ("than", "then"),
    ("then", "than"),
    ("who", "whom"),
    ("whom", "who"),
    ("less", "fewer"),
    ("fewer", "less"),
    ("amount", "number"),
    ("number", "amount"),
    ("farther", "further"),
    ("further", "farther"),
    ("lie", "lay"),
    ("lay", "lie"),
    ("sit", "set"),
    ("set", "sit"),
    ("rise", "raise"),
    ("raise", "rise"),
    ("bring", "take"),
    ("take", "bring"),
    ("come", "go"),
    ("go", "come"),
    ("can", "may"),
    ("may", "can"),
    ("shall", "will"),
    ("will", "shall"),
    ("should", "would"),
    ("would", "should"),
    ("could", "would"),
    ("would", "could"),
    ("might", "may"),
    ("may", "might"),
    ("must", "should"),
    ("should", "must"),
    ("ought", "should"),
    ("should", "ought"),
    ("used to", "use to"),
    ("use to", "used to"),
    ("supposed to", "suppose to"),
    ("suppose to", "supposed to"),
    ("going to", "gonna"),
    ("gonna", "going to"),
    ("want to", "wanna"),
    ("wanna", "want to"),
    ("have to", "hafta"),
    ("hafta", "have to"),
    ("got to", "gotta"),
    ("gotta", "got to"),
    ("need to", "needta"),
    ("needta", "need to"),
    ("try to", "tryna"),
    ("tryna", "try to"),
    ("let me", "lemme"),
    ("lemme", "let me"),
    ("give me", "gimme"),
    ("gimme", "give me"),
    ("tell me", "tellya"),
    ("tellya", "tell me"),
    ("don't know", "dunno"),
    ("dunno", "don't know"),
    ("I am", "I'm"),
    ("I'm", "I am"),
    ("you are", "you're"),
    ("you're", "you are"),
    ("he is", "he's"),
    ("he's", "he is"),
    ("she is", "she's"),
    ("she's", "she is"),
    ("it is", "it's"),
    ("it's", "it is"),
    ("we are", "we're"),
    ("we're", "we are"),
    ("they are", "they're"),
    ("they're", "they are"),
    ("I have", "I've"),
    ("I've", "I have"),
    ("you have", "you've"),
    ("you've", "you have"),
    ("he has", "he's"),
    ("he's", "he has"),
    ("she has", "she's"),
    ("she's", "she has"),
    ("it has", "it's"),
    ("it's", "it has"),
    ("we have", "we've"),
    ("we've", "we have"),
    ("they have", "they've"),
    ("they've", "they have"),
    ("I will", "I'll"),
    ("I'll", "I will"),
    ("you will", "you'll"),
    ("you'll", "you will"),
    ("he will", "he'll"),
    ("he'll", "he will"),
    ("she will", "she'll"),
    ("she'll", "she will"),
    ("it will", "it'll"),
    ("it'll", "it will"),
    ("we will", "we'll"),
    ("we'll", "we will"),
    ("they will", "they'll"),
    ("they'll", "they will"),
    ("I would", "I'd"),
    ("I'd", "I would"),
    ("you would", "you'd"),
    ("you'd", "you would"),
    ("he would", "he'd"),
    ("he'd", "he would"),
    ("she would", "she'd"),
    ("she'd", "she would"),
    ("it would", "it'd"),
    ("it'd", "it would"),
    ("we would", "we'd"),
    ("we'd", "we would"),
    ("they would", "they'd"),
    ("they'd", "they would"),
    ("I had", "I'd"),
    ("I'd", "I had"),
    ("you had", "you'd"),
    ("you'd", "you had"),
    ("he had", "he'd"),
    ("he'd", "he had"),
    ("she had", "she'd"),
    ("she'd", "she had"),
    ("it had", "it'd"),
    ("it'd", "it had"),
    ("we had", "we'd"),
    ("we'd", "we had"),
    ("they had", "they'd"),
    ("they'd", "they had"),
    ("I should", "I'd"),
    ("I'd", "I should"),
    ("you should", "you'd"),
    ("you'd", "you should"),
    ("he should", "he'd"),
    ("he'd", "he should"),
    ("she should", "she'd"),
    ("she'd", "she should"),
    ("it should", "it'd"),
    ("it'd", "it should"),
    ("we should", "we'd"),
    ("we'd", "we should"),
    ("they should", "they'd"),
    ("they'd", "they should"),
    ("I could", "I'd"),
    ("I'd", "I could"),
    ("you could", "you'd"),
    ("you'd", "you could"),
    ("he could", "he'd"),
    ("he'd", "he could"),
    ("she could", "she'd"),
    ("she'd", "she could"),
    ("it could", "it'd"),
    ("it'd", "it could"),
    ("we could", "we'd"),
    ("we'd", "we could"),
    ("they could", "they'd"),
    ("they'd", "they could"),
    ("I might", "I'd"),
    ("I'd", "I might"),
    ("you might", "you'd"),
    ("you'd", "you might"),
    ("he might", "he'd"),
    ("he'd", "he might"),
    ("she might", "she'd"),
    ("she'd", "she might"),
    ("it might", "it'd"),
    ("it'd", "it might"),
    ("we might", "we'd"),
    ("we'd", "we might"),
    ("they might", "they'd"),
    ("they'd", "they might"),
    ("I must", "I'd"),
    ("I'd", "I must"),
    ("you must", "you'd"),
    ("you'd", "you must"),
    ("he must", "he'd"),
    ("he'd", "he must"),
    ("she must", "she'd"),
    ("she'd", "she must"),
    ("it must", "it'd"),
    ("it'd", "it must"),
    ("we must", "we'd"),
    ("we'd", "we must"),
    ("they must", "they'd"),
    ("they'd", "they must"),
    ("I ought", "I'd"),
    ("I'd", "I ought"),
    ("you ought", "you'd"),
    ("you'd", "you ought"),
    ("he ought", "he'd"),
    ("he'd", "he ought"),
    ("she ought", "she'd"),
    ("she'd", "she ought"),
    ("it ought", "it'd"),
    ("it'd", "it ought"),
    ("we ought", "we'd"),
    ("we'd", "we ought"),
    ("they ought", "they'd"),
    ("they'd", "they ought"),
    ("I used to", "I'd"),
    ("I'd", "I used to"),
    ("you used to", "you'd"),
    ("you'd", "you used to"),
    ("he used to", "he'd"),
    ("he'd", "he used to"),
    ("she used to", "she'd"),
    ("she'd", "she used to"),
    ("it used to", "it'd"),
    ("it'd", "it used to"),
    ("we used to", "we'd"),
    ("we'd", "we used to"),
    ("they used to", "they'd"),
    ("they'd", "they used to"),
    ("I supposed to", "I'd"),
    ("I'd", "I supposed to"),
    ("you supposed to", "you'd"),
    ("you'd", "you supposed to"),
    ("he supposed to", "he'd"),
    ("he'd", "he supposed to"),
    ("she supposed to", "she'd"),
    ("she'd", "she supposed to"),
    ("it supposed to", "it'd"),
    ("it'd", "it supposed to"),
    ("we supposed to", "we'd"),
    ("we'd", "we supposed to"),
    ("they supposed to", "they'd"),
    ("they'd", "they supposed to"),
    ("I going to", "I'd"),
    ("I'd", "I going to"),
    ("you going to", "you'll"),
    ("you'll", "you going to"),
    ("he going to", "he'll"),
    ("he'll", "he going to"),
    ("she going to", "she'll"),
    ("she'll", "she going to"),
    ("it going to", "it'll"),
    ("it'll", "it going to"),
    ("we going to", "we'll"),
    ("we'll", "we going to"),
    ("they going to", "they'll"),
    ("they'll", "they going to"),
    ("I want to", "I'd"),
    ("I'd", "I want to"),
    ("you want to", "you'll"),
    ("you'll", "you want to"),
    ("he want to", "he'll"),
    ("he'll", "he want to"),
    ("she want to", "she'll"),
    ("she'll", "she want to"),
    ("it want to", "it'll"),
    ("it'll", "it want to"),
    ("we want to", "we'll"),
    ("we'll", "we want to"),
    ("they want to", "they'll"),
    ("they'll", "they want to"),
    ("I have to", "I'd"),
    ("I'd", "I have to"),
    ("you have to", "you'll"),
    ("you'll", "you have to"),
    ("he have to", "he'll"),
    ("he'll", "he have to"),
    ("she have to", "she'll"),
    ("she'll", "she have to"),
    ("it have to", "it'll"),
    ("it'll", "it have to"),
    ("we have to", "we'll"),
    ("we'll", "we have to"),
    ("they have to", "they'll"),
    ("they'll", "they have to"),
    ("I need to", "I'd"),
    ("I'd", "I need to"),
    ("you need to", "you'll"),
    ("you'll", "you need to"),
    ("he need to", "he'll"),
    ("he'll", "he need to"),
    ("she need to", "she'll"),
    ("she'll", "she need to"),
    ("it need to", "it'll"),
    ("it'll", "it need to"),
    ("we need to", "we'll"),
    ("we'll", "we need to"),
    ("they need to", "they'll"),
    ("they'll", "they need to"),
    ("I try to", "I'd"),
    ("I'd", "I try to"),
    ("you try to", "you'll"),
    ("you'll", "you try to"),
    ("he try to", "he'll"),
    ("he'll", "he try to"),
    ("she try to", "she'll"),
    ("she'll", "she try to"),
    ("it try to", "it'll"),
    ("it'll", "it try to"),
    ("we try to", "we'll"),
    ("we'll", "we try to"),
    ("they try to", "they'll"),
    ("they'll", "they try to"),
    ("I let me", "I'd"),
    ("I'd", "I let me"),
    ("you let me", "you'll"),
    ("you'll", "you let me"),
    ("he let me", "he'll"),
    ("he'll", "he let me"),
    ("she let me", "she'll"),
    ("she'll", "she let me"),
    ("it let me", "it'll"),
    ("it'll", "it let me"),
    ("we let me", "we'll"),
    ("we'll", "we let me"),
    ("they let me", "they'll"),
    ("they'll", "they let me"),
    ("I give me", "I'd"),
    ("I'd", "I give me"),
    ("you give me", "you'll"),
    ("you'll", "you give me"),
    ("he give me", "he'll"),
    ("he'll", "he give me"),
    ("she give me", "she'll"),
    ("she'll", "she give me"),
    ("it give me", "it'll"),
    ("it'll", "it give me"),
    ("we give me", "we'll"),
    ("we'll", "we give me"),
    ("they give me", "they'll"),
    ("they'll", "they give me"),
    ("I tell me", "I'd"),
    ("I'd", "I tell me"),
    ("you tell me", "you'll"),
    ("you'll", "you tell me"),
    ("he tell me", "he'll"),
    ("he'll", "he tell me"),
    ("she tell me", "she'll"),
    ("she'll", "she tell me"),
    ("it tell me", "it'll"),
    ("it'll", "it tell me"),
    ("we tell me", "we'll"),
    ("we'll", "we tell me"),
    ("they tell me", "they'll"),
    ("they'll", "they tell me"),
    ("I don't know", "I'd"),
    ("I'd", "I don't know"),
    ("you don't know", "you'll"),
    ("you'll", "you don't know"),
    ("he don't know", "he'll"),
    ("he'll", "he don't know"),
    ("she don't know", "she'll"),
    ("she'll", "she don't know"),
    ("it don't know", "it'll"),
    ("it'll", "it don't know"),
    ("we don't know", "we'll"),
    ("we'll", "we don't know"),
    ("they don't know", "they'll"),
    ("they'll", "they don't know"),
    ("I am", "I'm"),
    ("I'm", "I am"),
    ("you are", "you're"),
    ("you're", "you are"),
    ("he is", "he's"),
    ("he's", "he is"),
    ("she is", "she's"),
    ("she's", "she is"),
    ("it is", "it's"),
    ("it's", "it is"),
    ("we are", "we're"),
    ("we're", "we are"),
    ("they are", "they're"),
    ("they're", "they are"),
    ("I have", "I've"),
    ("I've", "I have"),
    ("you have", "you've"),
    ("you've", "you have"),
    ("he has", "he's"),
    ("he's", "he has"),
    ("she has", "she's"),
    ("she's", "she has"),
    ("it has", "it's"),
    ("it's", "it has"),
    ("we have", "we've"),
    ("we've", "we have"),
    ("they have", "they've"),
    ("they've", "they have"),
    ("I will", "I'll"),
    ("I'll", "I will"),
    ("you will", "you'll"),
    ("you'll", "you will"),
    ("he will", "he'll"),
    ("he'll", "he will"),
    ("she will", "she'll"),
    ("she'll", "she will"),
    ("it will", "it'll"),
    ("it'll", "it will"),
    ("we will", "we'll"),
    ("we'll", "we will"),
    ("they will", "they'll"),
    ("they'll", "they will"),
    ("I would", "I'd"),
    ("I'd", "I would"),
    ("you would", "you'd"),
    ("you'd", "you would"),
    ("he would", "he'd"),
    ("he'd", "he would"),
    ("she would", "she'd"),
    ("she'd", "she would"),
    ("it would", "it'd"),
    ("it'd", "it would"),
    ("we would", "we'd"),
    ("we'd", "we would"),
    ("they would", "they'd"),
    ("they'd", "they would"),
    ("I had", "I'd"),
    ("I'd", "I had"),
    ("you had", "you'd"),
    ("you'd", "you had"),
    ("he had", "he'd"),
    ("he'd", "he had"),
    ("she had", "she'd"),
    ("she'd", "she had"),
    ("it had", "it'd"),
    ("it'd", "it had"),
    ("we had", "we'd"),
    ("we'd", "we had"),
    ("they had", "they'd"),
    ("they'd", "they had"),
    ("I should", "I'd"),
    ("I'd", "I should"),
    ("you should", "you'd"),
    ("you'd", "you should"),
    ("he should", "he'd"),
    ("he'd", "he should"),
    ("she should", "she'd"),
    ("she'd", "she should"),
    ("it should", "it'd"),
    ("it'd", "it should"),
    ("we should", "we'd"),
    ("we'd", "we should"),
    ("they should", "they'd"),
    ("they'd", "they should"),
    ("I could", "I'd"),
    ("I'd", "I could"),
    ("you could", "you'd"),
    ("you'd", "you could"),
    ("he could", "he'd"),
    ("he'd", "he could"),
    ("she could", "she'd"),
    ("she'd", "she could"),
    ("it could", "it'd"),
    ("it'd", "it could"),
    ("we could", "we'd"),
    ("we'd", "we could"),
    ("they could", "they'd"),
    ("they'd", "they could"),
    ("I might", "I'd"),
    ("I'd", "I might"),
    ("you might", "you'd"),
    ("you'd", "you might"),
    ("he might", "he'd"),
    ("he'd", "he might"),
    ("she might", "she'd"),
    ("she'd", "she might"),
    ("it might", "it'd"),
    ("it'd", "it might"),
    ("we might", "we'd"),
    ("we'd", "we might"),
    ("they might", "they'd"),
    ("they'd", "they might"),
    ("I must", "I'd"),
    ("I'd", "I must"),
    ("you must", "you'd"),
    ("you'd", "you must"),
    ("he must", "he'd"),
    ("he'd", "he must"),
    ("she must", "she'd"),
    ("she'd", "she must"),
    ("it must", "it'd"),
    ("it'd", "it must"),
    ("we must", "we'd"),
    ("we'd", "we must"),
    ("they must", "they'd"),
    ("they'd", "they must"),
    ("I ought", "I'd"),
    ("I'd", "I ought"),
    ("you ought", "you'd"),
    ("you'd", "you ought"),
    ("he ought", "he'd"),
    ("he'd", "he ought"),
    ("she ought", "she'd"),
    ("she'd", "she ought"),
    ("it ought", "it'd"),
    ("it'd", "it ought"),
    ("we ought", "we'd"),
    ("we'd", "we ought"),
    ("they ought", "they'd"),
    ("they'd", "they ought"),
    ("I used to", "I'd"),
    ("I'd", "I used to"),
    ("you used to", "you'd"),
    ("you'd", "you used to"),
    ("he used to", "he'd"),
    ("he'd", "he used to"),
    ("she used to", "she'd"),
    ("she'd", "she used to"),
    ("it used to", "it'd"),
    ("it'd", "it used to"),
    ("we used to", "we'd"),
    ("we'd", "we used to"),
    ("they used to", "they'd"),
    ("they'd", "they used to"),
    ("I supposed to", "I'd"),
    ("I'd", "I supposed to"),
    ("you supposed to", "you'd"),
    ("you'd", "you supposed to"),
    ("he supposed to", "he'd"),
    ("he'd", "he supposed to"),
    ("she supposed to", "she'd"),
    ("she'd", "she supposed to"),
    ("it supposed to", "it'd"),
    ("it'd", "it supposed to"),
    ("we supposed to", "we'd"),
    ("we'd", "we supposed to"),
    ("they supposed to", "they'd"),
    ("they'd", "they supposed to"),
    ("I going to", "I'd"),
    ("I'd", "I going to"),
    ("you going to", "you'll"),
    ("you'll", "you going to"),
    ("he going to", "he'll"),
    ("he'll", "he going to"),
    ("she going to", "she'll"),
    ("she'll", "she going to"),
    ("it going to", "it'll"),
    ("it'll", "it going to"),
    ("we going to", "we'll"),
    ("we'll", "we going to"),
    ("they going to", "they'll"),
    ("they'll", "they going to"),
    ("I want to", "I'd"),
    ("I'd", "I want to"),
    ("you want to", "you'll"),
    ("you'll", "you want to"),
    ("he want to", "he'll"),
    ("he'll", "he want to"),
    ("she want to", "she'll"),
    ("she'll", "she want to"),
    ("it want to", "it'll"),
    ("it'll", "it want to"),
    ("we want to", "we'll"),
    ("we'll", "we want to"),
    ("they want to", "they'll"),
    ("they'll", "they want to"),
    ("I have to", "I'd"),
    ("I'd", "I have to"),
    ("you have to", "you'll"),
    ("you'll", "you have to"),
    ("he have to", "he'll"),
    ("he'll", "he have to"),
    ("she have to", "she'll"),
    ("she'll", "she have to"),
    ("it have to", "it'll"),
    ("it'll", "it have to"),
    ("we have to", "we'll"),
    ("we'll", "we have to"),
    ("they have to", "they'll"),
    ("they'll", "they have to"),
    ("I need to", "I'd"),
    ("I'd", "I need to"),
    ("you need to", "you'll"),
    ("you'll", "you need to"),
    ("he need to", "he'll"),
    ("he'll", "he need to"),
    ("she need to", "she'll"),
    ("she'll", "she need to"),
    ("it need to", "it'll"),
    ("it'll", "it need to"),
    ("we need to", "we'll"),
    ("we'll", "we need to"),
    ("they need to", "they'll"),
    ("they'll", "they need to"),
    ("I try to", "I'd"),
    ("I'd", "I try to"),
    ("you try to", "you'll"),
    ("you'll", "you try to"),
    ("he try to", "he'll"),
    ("he'll", "he try to"),
    ("she try to", "she'll"),
    ("she'll", "she try to"),
    ("it try to", "it'll"),
    ("it'll", "it try to"),
    ("we try to", "we'll"),
    ("we'll", "we try to"),
    ("they try to", "they'll"),
    ("they'll", "they try to"),
    ("I let me", "I'd"),
    ("I'd", "I let me"),
    ("you let me", "you'll"),
    ("you'll", "you let me"),
    ("he let me", "he'll"),
    ("he'll", "he let me"),
    ("she let me", "she'll"),
    ("she'll", "she let me"),
    ("it let me", "it'll"),
    ("it'll", "it let me"),
    ("we let me", "we'll"),
    ("we'll", "we let me"),
    ("they let me", "they'll"),
    ("they'll", "they let me"),
    ("I give me", "I'd"),
    ("I'd", "I give me"),
    ("you give me", "you'll"),
    ("you'll", "you give me"),
    ("he give me", "he'll"),
    ("he'll", "he give me"),
    ("she give me", "she'll"),
    ("she'll", "she give me"),
    ("it give me", "it'll"),
    ("it'll", "it give me"),
    ("we give me", "we'll"),
    ("we'll", "we give me"),
    ("they give me", "they'll"),
    ("they'll", "they give me"),
    ("I tell me", "I'd"),
    ("I'd", "I tell me"),
    ("you tell me", "you'll"),
    ("you'll", "you tell me"),
    ("he tell me", "he'll"),
    ("he'll", "he tell me"),
    ("she tell me", "she'll"),
    ("she'll", "she tell me"),
    ("it tell me", "it'll"),
    ("it'll", "it tell me"),
    ("we tell me", "we'll"),
    ("we'll", "we tell me"),
    ("they tell me", "they'll"),
    ("they'll", "they tell me"),
    ("I don't know", "I'd"),
    ("I'd", "I don't know"),
    ("you don't know", "you'll"),
    ("you'll", "you don't know"),
    ("he don't know", "he'll"),
    ("he'll", "he don't know"),
    ("she don't know", "she'll"),
    ("she'll", "she don't know"),
    ("it don't know", "it'll"),
    ("it'll", "it don't know"),
    ("we don't know", "we'll"),
    ("we'll", "we don't know"),
    ("they don't know", "they'll"),
    ("they'll", "they don't know"),
]

def introduce_grammatical_errors(text: str, num_errors: int = 2) -> str:
    """Introduce grammatical errors into text."""
    words = text.split()
    error_count = 0
    error_positions = set()
    
    # Try to introduce errors
    attempts = 0
    max_attempts = len(words) * 2
    
    while error_count < num_errors and attempts < max_attempts:
        attempts += 1
        i = random.randint(0, len(words) - 1)
        
        if i in error_positions:
            continue
        
        word_clean = re.sub(r'[^\w]', '', words[i]).lower()
        
        # Check if word matches any error pattern
        for correct, wrong in GRAMMATICAL_ERRORS:
            if word_clean == correct.lower():
                # Preserve punctuation
                original_word = words[i]
                if original_word[0].isupper():
                    words[i] = wrong.capitalize() + original_word[len(word_clean):]
                else:
                    words[i] = wrong + original_word[len(word_clean):]
                error_count += 1
                error_positions.add(i)
                break
    
    return ' '.join(words)


def format_answer_file(document_id: str, responses: List[Dict], has_errors: bool = False) -> str:
    """Format an answer file similar to answer_key_answerkey.pdf."""
    lines = []
    
    # Header
    lines.append(f"{document_id.replace('_', ' ').title()} Quiz")
    lines.append("Answer Key")
    lines.append("")
    
    # Group by question type
    mcq_questions = []
    tf_questions = []
    long_questions = []
    
    for resp in responses:
        q_type = resp.get('question_type', '').upper()
        if q_type == 'MCQ':
            mcq_questions.append(resp)
        elif q_type == 'TF':
            tf_questions.append(resp)
        elif q_type == 'LONG':
            long_questions.append(resp)
    
    # Multiple Choice Questions
    if mcq_questions:
        lines.append("Multiple Choice Questions")
        lines.append("")
        for resp in sorted(mcq_questions, key=lambda x: x.get('question_number', 0)):
            q_num = resp.get('question_number', 0)
            gold = resp.get('gold_answer', 'N/A')
            ai_answer = resp.get('ai_answer') or 'N/A'
            
            if not isinstance(ai_answer, str):
                ai_answer = str(ai_answer) if ai_answer else 'N/A'
            
            # Extract option letter if available
            option_match = re.search(r'\(([a-d])\)', ai_answer, re.IGNORECASE) if isinstance(ai_answer, str) else None
            if option_match:
                option = option_match.group(1).upper()
            else:
                option = gold if gold and gold in ['A', 'B', 'C', 'D'] else 'A'
            
            # Get answer text (remove the option marker)
            answer_text = re.sub(r'\([a-d]\)\s*', '', ai_answer, flags=re.IGNORECASE).strip() if isinstance(ai_answer, str) else str(ai_answer)
            if not answer_text:
                answer_text = str(ai_answer) if ai_answer else 'N/A'
            
            if has_errors and random.random() < 0.4:
                answer_text = introduce_grammatical_errors(answer_text, num_errors=random.randint(1, 2))
            
            lines.append(f"{q_num}. ({option}) {answer_text}")
            lines.append("")
    
    # True/False Questions
    if tf_questions:
        lines.append("True / False Questions")
        lines.append("")
        for resp in sorted(tf_questions, key=lambda x: x.get('question_number', 0)):
            q_num = resp.get('question_number', 0)
            ai_answer = resp.get('ai_answer') or 'N/A'
            
            if not isinstance(ai_answer, str):
                ai_answer = str(ai_answer) if ai_answer else 'N/A'
            
            # Extract True/False
            if isinstance(ai_answer, str) and 'true' in ai_answer.lower() and 'false' not in ai_answer.lower():
                answer = "True"
            elif isinstance(ai_answer, str) and 'false' in ai_answer.lower():
                answer = "False"
            else:
                answer = str(ai_answer).strip() if ai_answer else 'N/A'
            
            if has_errors and random.random() < 0.4:
                # For TF, just add a typo or spacing issue
                if random.random() < 0.5:
                    answer = answer.replace('True', 'Ture').replace('False', 'Flase')
            
            lines.append(f"{q_num}. {answer}")
            lines.append("")
    
    # Long Form Questions
    if long_questions:
        lines.append("Long Form Response Questions")
        lines.append("")
        for resp in sorted(long_questions, key=lambda x: x.get('question_number', 0)):
            q_num = resp.get('question_number', 0)
            ai_answer = resp.get('ai_answer') or 'N/A'
            
            if not isinstance(ai_answer, str):
                ai_answer = str(ai_answer) if ai_answer else 'N/A'
            
            # Clean up code blocks
            answer_text = ai_answer.replace('```python', '').replace('```', '').strip() if isinstance(ai_answer, str) else str(ai_answer)
            
            if has_errors and random.random() < 0.5:
                answer_text = introduce_grammatical_errors(answer_text, num_errors=random.randint(2, 3))
            
            lines.append(f"{q_num}. Sample answer:")
            lines.append("")
            # Split long answers into paragraphs
            if len(answer_text) > 100:
                sentences = re.split(r'([.!?]\s+)', answer_text)
                current_para = []
                for i in range(0, len(sentences), 2):
                    if i < len(sentences):
                        sentence = sentences[i]
                        if i + 1 < len(sentences):
                            sentence += sentences[i + 1]
                        current_para.append(sentence)
                        if len(' '.join(current_para)) > 80:
                            lines.append(''.join(current_para))
                            lines.append("")
                            current_para = []
                if current_para:
                    lines.append(''.join(current_para))
            else:
                lines.append(answer_text)
            lines.append("")
    
    return '\n'.join(lines)

def main():
    """Main function to generate human answer files."""
    output_dir = Path("human_responses")
    output_dir.mkdir(exist_ok=True)
    
    detection_dir = Path("output_detection")
    
    # Find all response JSON files
    response_files = list(detection_dir.rglob("*_responses.json"))
    
    print(f"Found {len(response_files)} response files")
    
    # Select files to add errors to (10-15 files)
    num_files_with_errors = random.randint(10, 15)
    files_with_errors = set(random.sample(response_files, min(num_files_with_errors, len(response_files))))
    
    generated_count = 0
    error_count = 0
    
    for resp_file in response_files:
        try:
            with open(resp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            document_id = data.get('document_id', 'unknown')
            responses = data.get('responses', [])
            
            if not responses:
                continue
            
            # Determine if this file should have errors
            has_errors = resp_file in files_with_errors
            
            # Generate answer file
            answer_text = format_answer_file(document_id, responses, has_errors=has_errors)
            
            # Create filename
            filename = f"{document_id}_answer_key.txt"
            output_path = output_dir / filename
            
            # Handle duplicates
            counter = 1
            while output_path.exists():
                filename = f"{document_id}_answer_key_{counter}.txt"
                output_path = output_dir / filename
                counter += 1
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(answer_text)
            
            generated_count += 1
            if has_errors:
                error_count += 1
                print(f"Generated {filename} (WITH ERRORS)")
            else:
                print(f"Generated {filename}")
        
        except Exception as e:
            print(f"Error processing {resp_file}: {e}")
            continue
    
    print(f"\nGenerated {generated_count} answer files")
    print(f"Files with grammatical errors: {error_count}")

if __name__ == "__main__":
    main()

