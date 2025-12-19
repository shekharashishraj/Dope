#!/usr/bin/env python3
"""Script to merge perturbations back into original JSON files."""

import json
import sys
from pathlib import Path

def merge_perturbations(original_json_path, perturbation_json_path, output_path):
    """Merge perturbations into original JSON and save."""
    # Load original
    with open(original_json_path, 'r') as f:
        original_data = json.load(f)
    
    # Load perturbations
    with open(perturbation_json_path, 'r') as f:
        perturbations = json.load(f)
    
    # Add perturbations to questions
    for question in original_data.get('questions', []):
        q_num = question.get('question_number')
        if q_num is not None and str(q_num) in perturbations:
            question['perturbations'] = perturbations[str(q_num)]
        else:
            question['perturbations'] = []
    
    # Save merged data
    with open(output_path, 'w') as f:
        json.dump(original_data, f, indent=2)
    
    print(f"Merged and saved to {output_path}")

def main():
    # Define the mappings
    mappings = [
        {
            'original': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output/astronomy/graduate/JSON_output/astronomy_graduate_doc_02.json',
            'perturbation': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/astronomy/graduate/astronomy_graduate_doc_02_perturbation.json',
            'output': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/astronomy/graduate/astronomy_graduate_doc_02_perturbation.json'
        },
        {
            'original': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output/astronomy/graduate/JSON_output/astronomy_graduate_doc_03.json',
            'perturbation': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/astronomy/graduate/astronomy_graduate_doc_03_perturbation.json',
            'output': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/astronomy/graduate/astronomy_graduate_doc_03_perturbation.json'
        },
        {
            'original': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output/astronomy/graduate/JSON_output/astronomy_graduate_doc_04.json',
            'perturbation': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/astronomy/graduate/astronomy_graduate_doc_04_perturbation.json',
            'output': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/astronomy/graduate/astronomy_graduate_doc_04_perturbation.json'
        },
        {
            'original': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output/cybersecurity/undergraduate/JSON_output/cybersecurity_undergraduate_doc_01.json',
            'perturbation': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/cybersecurity/undergraduate/cybersecurity_undergraduate_doc_01/cybersecurity_undergraduate_doc_01_perturbation.json',
            'output': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/cybersecurity/undergraduate/cybersecurity_undergraduate_doc_01/cybersecurity_undergraduate_doc_01_perturbation.json'
        },
        {
            'original': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output/cybersecurity/undergraduate/JSON_output/cybersecurity_undergraduate_doc_01.json',
            'perturbation': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/cybersecurity/undergraduate/cybersecurity_undergraduate_doc_01_perturbation.json',
            'output': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/cybersecurity/undergraduate/cybersecurity_undergraduate_doc_01_perturbation.json'
        },
        {
            'original': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output/cybersecurity/undergraduate/JSON_output/cybersecurity_undergraduate_doc_02.json',
            'perturbation': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/cybersecurity/undergraduate/cybersecurity_undergraduate_doc_02_perturbation.json',
            'output': '/Users/ShahYash/Desktop/fairtest_html/IGSHIELD/output_perturbation/20251218_141143/cybersecurity/undergraduate/cybersecurity_undergraduate_doc_02_perturbation.json'
        }
    ]
    
    for mapping in mappings:
        if Path(mapping['original']).exists() and Path(mapping['perturbation']).exists():
            merge_perturbations(mapping['original'], mapping['perturbation'], mapping['output'])
        else:
            print(f"Missing files for {mapping['perturbation']}")

if __name__ == "__main__":
    main()