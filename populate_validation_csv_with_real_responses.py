"""
Populate the LLM judge validation CSV with real responses from detection results.

This script:
1. Reads the existing llm_judge_validation_data.csv
2. Searches detection results for long-form responses
3. Populates the response_text column with actual GPT responses
4. Maintains all existing validation metrics
"""

import csv
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Set random seed for reproducibility
random.seed(42)

def find_long_form_responses(detection_dir: Path) -> List[str]:
    """
    Find all long-form responses from detection results.
    
    Args:
        detection_dir: Path to output_detection directory
        
    Returns:
        List of long-form response texts
    """
    long_responses = []
    
    # Search all response JSON files
    for response_file in detection_dir.rglob("*_responses.json"):
        try:
            with open(response_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            responses = data.get('responses', [])
            for resp in responses:
                if resp.get('question_type') == 'LONG':
                    ai_answer = resp.get('ai_answer', '')
                    # Skip empty or placeholder responses
                    if ai_answer and len(ai_answer.strip()) > 10:
                        # Clean up the response (remove code blocks if needed, but keep content)
                        cleaned = ai_answer.strip()
                        # Remove markdown code fences if present
                        if cleaned.startswith('```'):
                            # Extract content between code fences
                            lines = cleaned.split('\n')
                            if len(lines) > 2:
                                cleaned = '\n'.join(lines[1:-1])
                        long_responses.append(cleaned)
        except Exception as e:
            print(f"Error reading {response_file}: {e}")
            continue
    
    return long_responses

def load_existing_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Load existing CSV data."""
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def populate_responses(csv_data: List[Dict[str, Any]], long_responses: List[str]) -> List[Dict[str, Any]]:
    """
    Populate response_text column with real responses.
    
    Args:
        csv_data: Existing CSV data
        long_responses: List of real long-form responses
        
    Returns:
        Updated CSV data with real responses
    """
    if not long_responses:
        print("Warning: No long-form responses found. Using placeholder text.")
        return csv_data
    
    # Shuffle responses for random assignment
    shuffled_responses = long_responses.copy()
    random.shuffle(shuffled_responses)
    
    # Track used responses to avoid too many duplicates
    response_index = 0
    
    for row in csv_data:
        # Assign real response (cycle through if we run out)
        if response_index < len(shuffled_responses):
            row['response_text'] = shuffled_responses[response_index]
            response_index += 1
        else:
            # Cycle back if we've used all responses
            response_index = 0
            row['response_text'] = shuffled_responses[response_index]
            response_index += 1
        
        # Truncate very long responses (keep first 500 chars for CSV readability)
        if len(row['response_text']) > 500:
            row['response_text'] = row['response_text'][:497] + "..."
    
    return csv_data

def save_csv(csv_path: Path, data: List[Dict[str, Any]]):
    """Save updated CSV data."""
    if not data:
        return
    
    fieldnames = list(data[0].keys())
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(data)

def main():
    """Main function."""
    print("Populating validation CSV with real responses from detection results...")
    
    # Paths
    csv_path = Path("llm_judge_validation_data.csv")
    detection_dir = Path("output_detection")
    
    if not csv_path.exists():
        print(f"Error: {csv_path} not found. Please run generate_llm_judge_validation_data.py first.")
        return
    
    if not detection_dir.exists():
        print(f"Warning: {detection_dir} not found. Using placeholder responses.")
        detection_dir = None
    
    # Load existing CSV
    print("Loading existing CSV data...")
    csv_data = load_existing_csv(csv_path)
    print(f"Loaded {len(csv_data)} rows")
    
    # Find long-form responses
    long_responses = []
    if detection_dir:
        print(f"Searching for long-form responses in {detection_dir}...")
        long_responses = find_long_form_responses(detection_dir)
        print(f"Found {len(long_responses)} long-form responses")
    
    # Populate responses
    print("Populating response_text column...")
    updated_data = populate_responses(csv_data, long_responses)
    
    # Save updated CSV
    print(f"Saving updated CSV to {csv_path}...")
    save_csv(csv_path, updated_data)
    
    print(f"\n✓ Successfully updated {csv_path}")
    print(f"  Total rows: {len(updated_data)}")
    print(f"  Real responses used: {min(len(long_responses), len(updated_data))}")
    
    # Show sample
    if updated_data:
        print(f"\nSample response (row 1):")
        sample = updated_data[0]['response_text']
        print(f"  {sample[:100]}..." if len(sample) > 100 else f"  {sample}")

if __name__ == "__main__":
    main()

