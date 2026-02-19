#!/usr/bin/env python3
"""Compute query edit distance for all detection perturbation mappings."""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein distance using dynamic programming."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def load_all_perturbations(perturbation_dir: Path) -> List[Dict[str, Any]]:
    """Load all perturbation mappings from generation_results.json files."""
    all_mappings = []
    # Look for generation_results.json files
    json_files = list(perturbation_dir.rglob("generation_results.json"))
    
    print(f"Found {len(json_files)} generation_results.json files")
    
    loaded_count = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Structure: { "doc_perturbation.json": { "methods": { "method_name": { "metadata": { "replacements": [...] } } } } }
            for doc_key, doc_data in data.items():
                if not isinstance(doc_data, dict) or 'methods' not in doc_data:
                    continue
                
                docid = doc_data.get('docid', 'unknown')
                output_meta = doc_data.get('output_metadata', {})
                domain = output_meta.get('subject', doc_data.get('domain', 'unknown'))
                academic_level = output_meta.get('level', doc_data.get('academic_level', 'unknown'))
                
                # Extract from all methods
                for method_name, method_data in doc_data.get('methods', {}).items():
                    if not isinstance(method_data, dict) or 'metadata' not in method_data:
                        continue
                    
                    metadata = method_data.get('metadata', {})
                    replacements = metadata.get('replacements', [])
                    
                    for repl in replacements:
                        orig = repl.get('original', '')
                        repl_text = repl.get('replacement', '')
                        if not orig or not repl_text:
                            continue
                        
                        mapping = {
                            'docid': docid,
                            'domain': domain,
                            'academic_level': academic_level,
                            'question_number': repl.get('question_number'),
                            'question_type': None,  # Not available in generation_results
                            'method': method_name,
                            'original_substring': orig,
                            'replacement_substring': repl_text,
                            'start_pos': repl.get('position', [None, None])[0] if isinstance(repl.get('position'), list) else None,
                            'end_pos': repl.get('position', [None, None])[1] if isinstance(repl.get('position'), list) else None,
                            'json_file': str(json_file)
                        }
                        all_mappings.append(mapping)
                
                loaded_count += 1
        except Exception as e:
            print(f"Error loading {json_file}: {e}", file=sys.stderr)
            continue
    
    print(f"Loaded perturbations from {loaded_count} files")
    return all_mappings


def compute_edit_distances(mappings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute edit distance for each mapping."""
    results = []
    
    for mapping in mappings:
        orig = mapping['original_substring']
        repl = mapping['replacement_substring']
        
        # Compute edit distance
        ed = levenshtein_distance(orig, repl)
        
        # Additional metrics
        orig_len = len(orig)
        repl_len = len(repl)
        length_diff = abs(orig_len - repl_len)
        max_len = max(orig_len, repl_len)
        normalized_ed = ed / max_len if max_len > 0 else 0
        
        result = {
            **mapping,
            'edit_distance': ed,
            'original_length': orig_len,
            'replacement_length': repl_len,
            'length_difference': length_diff,
            'normalized_edit_distance': normalized_ed
        }
        results.append(result)
    
    return results


def generate_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate statistics from edit distance results."""
    if not results:
        return {}
    
    edit_distances = [r['edit_distance'] for r in results]
    normalized_eds = [r['normalized_edit_distance'] for r in results]
    length_diffs = [r['length_difference'] for r in results]
    orig_lengths = [r['original_length'] for r in results]
    repl_lengths = [r['replacement_length'] for r in results]
    
    # By question type
    by_type = defaultdict(list)
    for r in results:
        qtype = r.get('question_type', 'unknown')
        by_type[qtype].append(r['edit_distance'])
    
    # By domain
    by_domain = defaultdict(list)
    for r in results:
        domain = r.get('domain', 'unknown')
        by_domain[domain].append(r['edit_distance'])
    
    # By academic level
    by_level = defaultdict(list)
    for r in results:
        level = r.get('academic_level', 'unknown')
        by_level[level].append(r['edit_distance'])
    
    # By method
    by_method = defaultdict(list)
    for r in results:
        method = r.get('method', 'unknown')
        by_method[method].append(r['edit_distance'])
    
    def calc_stats(vals):
        if not vals:
            return {}
        sorted_vals = sorted(vals)
        n = len(vals)
        mean = sum(vals) / n
        median = sorted_vals[n // 2] if n > 0 else 0
        variance = sum((x - mean) ** 2 for x in vals) / n
        std = variance ** 0.5
        return {
            'count': n,
            'mean': mean,
            'median': median,
            'min': min(vals),
            'max': max(vals),
            'std': std,
            'q1': sorted_vals[n // 4] if n >= 4 else sorted_vals[0],
            'q3': sorted_vals[3 * n // 4] if n >= 4 else sorted_vals[-1]
        }
    
    stats = {
        'total_mappings': len(results),
        'overall': {
            **calc_stats(edit_distances),
            'mean_normalized_ed': sum(normalized_eds) / len(normalized_eds),
            'median_normalized_ed': sorted(normalized_eds)[len(normalized_eds) // 2],
            'mean_length_difference': sum(length_diffs) / len(length_diffs),
            'mean_original_length': sum(orig_lengths) / len(orig_lengths),
            'mean_replacement_length': sum(repl_lengths) / len(repl_lengths),
        },
        'by_question_type': {
            qtype: calc_stats(vals)
            for qtype, vals in by_type.items()
        },
        'by_domain': {
            domain: calc_stats(vals)
            for domain, vals in by_domain.items()
        },
        'by_academic_level': {
            level: calc_stats(vals)
            for level, vals in by_level.items()
        },
        'by_method': {
            method: calc_stats(vals)
            for method, vals in by_method.items()
        }
    }
    
    return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute edit distance for perturbation mappings")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="output_perturbation",
        help="Directory containing perturbation JSON files (default: output_perturbation)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="edit_distance_results.json",
        help="Output JSON file for results (default: edit_distance_results.json)"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only output statistics, not individual mappings"
    )
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Load all perturbations
    print("Loading perturbation mappings...")
    mappings = load_all_perturbations(input_dir)
    print(f"Loaded {len(mappings)} perturbation mappings")
    
    if len(mappings) == 0:
        print("No perturbations found!")
        print(f"Tried to find files in: {input_dir}")
        print("Looking for files with 'questions' containing 'perturbations' with 'original_substring' and 'replacement_substring'")
        sys.exit(1)
    
    # Compute edit distances
    print("Computing edit distances...")
    results = compute_edit_distances(mappings)
    
    # Generate statistics
    print("Generating statistics...")
    stats = generate_statistics(results)
    
    # Save results
    output_data = {
        'statistics': stats,
        'mappings': [] if args.stats_only else results
    }
    
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print detailed statistics
    print(f"\n{'='*80}")
    print(f"EDIT DISTANCE STATISTICS")
    print(f"{'='*80}\n")
    
    print(f"Total Mappings: {stats['total_mappings']}\n")
    
    print(f"{'OVERALL STATISTICS':-^80}")
    overall = stats['overall']
    print(f"  Edit Distance:")
    print(f"    Mean:   {overall['mean']:.2f}")
    print(f"    Median: {overall['median']:.2f}")
    print(f"    Std:    {overall['std']:.2f}")
    print(f"    Min:    {overall['min']}")
    print(f"    Max:    {overall['max']}")
    print(f"    Q1:     {overall['q1']}")
    print(f"    Q3:     {overall['q3']}")
    print(f"\n  Normalized Edit Distance:")
    print(f"    Mean:   {overall['mean_normalized_ed']:.3f}")
    print(f"    Median: {overall['median_normalized_ed']:.3f}")
    print(f"\n  Length Metrics:")
    print(f"    Mean Original Length:     {overall['mean_original_length']:.2f}")
    print(f"    Mean Replacement Length: {overall['mean_replacement_length']:.2f}")
    print(f"    Mean Length Difference:  {overall['mean_length_difference']:.2f}")
    
    print(f"\n{'BY QUESTION TYPE':-^80}")
    for qtype, type_stats in sorted(stats['by_question_type'].items()):
        print(f"\n  {qtype}:")
        print(f"    Count:  {type_stats['count']}")
        print(f"    Mean:   {type_stats['mean']:.2f}")
        print(f"    Median: {type_stats['median']:.2f}")
        print(f"    Std:    {type_stats['std']:.2f}")
        print(f"    Min:    {type_stats['min']}")
        print(f"    Max:    {type_stats['max']}")
    
    print(f"\n{'BY DOMAIN':-^80}")
    for domain, domain_stats in sorted(stats['by_domain'].items()):
        print(f"\n  {domain}:")
        print(f"    Count:  {domain_stats['count']}")
        print(f"    Mean:   {domain_stats['mean']:.2f}")
        print(f"    Median: {domain_stats['median']:.2f}")
        print(f"    Min:    {domain_stats['min']}")
        print(f"    Max:    {domain_stats['max']}")
    
    print(f"\n{'BY ACADEMIC LEVEL':-^80}")
    for level, level_stats in sorted(stats['by_academic_level'].items()):
        print(f"\n  {level}:")
        print(f"    Count:  {level_stats['count']}")
        print(f"    Mean:   {level_stats['mean']:.2f}")
        print(f"    Median: {level_stats['median']:.2f}")
        print(f"    Min:    {level_stats['min']}")
        print(f"    Max:    {level_stats['max']}")
    
    print(f"\n{'BY METHOD':-^80}")
    for method, method_stats in sorted(stats['by_method'].items()):
        print(f"\n  {method}:")
        print(f"    Count:  {method_stats['count']}")
        print(f"    Mean:   {method_stats['mean']:.2f}")
        print(f"    Median: {method_stats['median']:.2f}")
        print(f"    Std:    {method_stats['std']:.2f}")
        print(f"    Min:    {method_stats['min']}")
        print(f"    Max:    {method_stats['max']}")
    
    print(f"\n{'='*80}")
    print(f"✓ Results saved to {output_path}")
    print(f"{'='*80}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
