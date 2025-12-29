#!/usr/bin/env python3
"""Analyze why font_attack is not being generated for doc_01."""

import json
from pathlib import Path
from collections import Counter

# Find the perturbation JSON file
perturbation_file = Path("output_perturbation/20251228_144124/cybersecurity/undergraduate/cybersecurity_undergraduate_doc_01/cybersecurity_undergraduate_doc_01_perturbation.json")

if not perturbation_file.exists():
    print(f"ERROR: File not found: {perturbation_file}")
    exit(1)

# Load the data
with open(perturbation_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("ANALYSIS: Font Attack Generation Issue")
print("=" * 80)
print(f"\nDocument: {data.get('docid', 'unknown')}")
print(f"Total questions: {len(data.get('questions', []))}")

# Analyze perturbations per question
questions = data.get('questions', [])
pert_counts = []
questions_with_perturbations = 0

for i, q in enumerate(questions):
    pert_count = len(q.get('perturbations', []))
    pert_counts.append(pert_count)
    if pert_count > 0:
        questions_with_perturbations += 1
    
    print(f"\nQuestion {i+1} (Q{q.get('question_number', '?')}):")
    print(f"  Type: {q.get('question_type', 'unknown')}")
    print(f"  Perturbations: {pert_count}")
    
    if pert_count == 0:
        print("  ⚠️  NO PERTURBATIONS - This question will be skipped!")
    elif pert_count < 3:
        print(f"  ⚠️  Only {pert_count} perturbation(s) - Will only generate {pert_count} font attack PDF(s)")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total questions: {len(questions)}")
print(f"Questions with perturbations: {questions_with_perturbations}")
print(f"Questions without perturbations: {len(questions) - questions_with_perturbations}")

if pert_counts:
    counter = Counter(pert_counts)
    print(f"\nPerturbation count distribution:")
    for count, num_questions in sorted(counter.items()):
        print(f"  {count} perturbation(s): {num_questions} question(s)")

# Simulate the orchestrator logic
print("\n" + "=" * 80)
print("SIMULATED ORCHESTRATOR LOGIC")
print("=" * 80)

for pert_idx in range(1, 4):
    filtered_count = 0
    for q in questions:
        q_perturbations = q.get('perturbations', [])
        if len(q_perturbations) >= pert_idx:
            filtered_count += 1
    
    print(f"\nPerturbation index {pert_idx}:")
    print(f"  Questions with >= {pert_idx} perturbations: {filtered_count}")
    if filtered_count == 0:
        print(f"  ❌ SKIPPED - No questions have {pert_idx} or more perturbations")
    else:
        print(f"  ✓ Would generate font attack PDF for {filtered_count} question(s)")

# Check if font_attack folder should exist
total_perturbations_generated = sum(1 for pert_idx in range(1, 4) 
                                   for q in questions 
                                   if len(q.get('perturbations', [])) >= pert_idx)

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
if total_perturbations_generated == 0:
    print("❌ NO FONT ATTACK PDFs WOULD BE GENERATED")
    print("   Reason: No questions have any perturbations, or all questions")
    print("   have fewer perturbations than required.")
else:
    print(f"✓ {total_perturbations_generated} font attack PDF(s) should be generated")
    if total_perturbations_generated < 3 * questions_with_perturbations:
        print("   Note: Not all 3 perturbation indices will generate PDFs")
        print("   because some questions have fewer than 3 perturbations.")

