"""Stage 3 (prevention): run existing detection/eval components on prevention outputs.

We keep Stage 3 logic intact by reusing:
- ResponseCollector
- SignatureMatcher
- MetricsCalculator

This script exists because `src/detection/test.py` is hardcoded to the
`output_attacked_pdfs/` directory layout.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Add repo root to sys.path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# These imports require the full Python deps (`pip install -r requirements.txt`).
try:
    from src.config import Config
    from src.detection.response_collector import ResponseCollector
    from src.detection.anthropic_response_collector import AnthropicResponseCollector
    from src.detection.signature_matcher import SignatureMatcher
    from src.detection.metrics_calculator import MetricsCalculator
    from src.models.perturbation import Document
    from .prevention_matcher import PreventionMatcher
    from .prevention_metrics_calculator import PreventionMetricsCalculator
    from tqdm import tqdm
except ModuleNotFoundError as e:
    raise SystemExit(
        f"Missing dependency: {e}\n"
        "Please ensure you have installed dependencies:\n"
        "  python3 -m pip install -r requirements.txt\n"
    )


def find_prevention_pdfs(prevention_pdf_dir: Path, method_filter: Optional[str] = None) -> List[Dict[str, Path]]:
    pdfs: List[Dict[str, Path]] = []
    for pdf_file in prevention_pdf_dir.rglob("*.pdf"):
        if "compile.log" in str(pdf_file):
            continue
        if method_filter and method_filter not in str(pdf_file):
            continue

        # Find matching prevention JSON by walking upwards:
        # .../<variant_file>.pdf lives under .../<doc>/<method>/; JSON is expected
        # to be in the corresponding prevention perturbation folder the user provides.
        pdfs.append({"pdf": pdf_file})
    return pdfs


def build_json_index(prevention_json_root: Path) -> Dict[str, Path]:
    """Index prevention perturbation JSONs by (docid, variant)."""

    idx: Dict[str, Path] = {}
    for jp in prevention_json_root.rglob("*_prevention_perturbation_*.json"):
        name = jp.name
        # <docid>_prevention_perturbation_<variant>.json
        parts = name.split("_prevention_perturbation_")
        if len(parts) != 2:
            continue
        docid = parts[0]
        variant = parts[1].replace(".json", "")
        idx[f"{docid}::{variant}"] = jp
    return idx


def infer_docid_variant_from_pdf(pdf_path: Path) -> Optional[Dict[str, str]]:
    # Expect patterns like:
    # biology_graduate_doc_03_refusal_string_font_attack.pdf
    # biology_graduate_doc_03_icw.pdf (ICW has no variant)
    stem = pdf_path.stem
    
    # Check for ICW (no variant)
    if stem.endswith("_icw"):
        docid = stem[:-4]  # Remove "_icw"
        return {"docid": docid, "variant": None, "method": "icw"}
    
    # Try to extract last two components: <variant>_<method>
    # docid may itself contain underscores; we use known variants.
    for variant in ["gibberish", "refusal_string"]:
        if f"_{variant}_" in stem:
            docid = stem.split(f"_{variant}_")[0]
            method = stem.split(f"_{variant}_", 1)[1]
            return {"docid": docid, "variant": variant, "method": method}
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 3 (prevention): evaluate prevention PDFs with existing matcher/metrics")
    parser.add_argument("--pdfs", type=str, required=True, help="Directory containing prevention attacked PDFs")
    parser.add_argument("--prevention-jsons", type=str, required=True, help="Directory containing prevention perturbation JSONs")
    parser.add_argument("--model", type=str, default="gpt-4o", help="Model to use for response collection (OpenAI or Anthropic Claude)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of PDFs to evaluate")
    parser.add_argument("--one-per-domain-level", action="store_true", help="Process only 1 document per domain-level combination")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Path to config file")
    parser.add_argument("--output", type=str, default=None, help="Output directory (default: output_detection/<timestamp>)")
    parser.add_argument("--method", type=str, default=None, help="Filter by method substring (e.g. dual_layer, font_attack)")

    args = parser.parse_args()

    config = Config.from_yaml(args.config)

    pdf_dir = Path(args.pdfs).resolve()
    json_root = Path(args.prevention_jsons).resolve()
    if not pdf_dir.exists():
        raise SystemExit(f"PDF directory not found: {pdf_dir}")
    if not json_root.exists():
        raise SystemExit(f"Prevention JSON directory not found: {json_root}")

    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output_detection") / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    pdfs = find_prevention_pdfs(pdf_dir, method_filter=args.method)
    if args.limit:
        pdfs = pdfs[: args.limit]
    if not pdfs:
        raise SystemExit("No PDFs found to evaluate.")

    json_index = build_json_index(json_root)

    # Use PreventionMetricsCalculator for prevention-specific metrics
    calculator = PreventionMetricsCalculator()
    
    # Set up logging
    progress_logger = logging.getLogger(__name__)
    progress_logger.setLevel(logging.INFO)
    
    # Determine which collector to use based on model name
    is_anthropic = args.model.startswith("claude") or args.model.startswith("opus")
    collector_class = AnthropicResponseCollector if is_anthropic else ResponseCollector
    collector = collector_class(config, model=args.model)

    # Get rate limiting delay from config
    delay_between_requests = getattr(config.performance, 'delay_between_requests', 0.1) if hasattr(config, 'performance') else 0.1

    flat_results: List[Dict[str, Any]] = []
    skipped = 0
    errors = 0
    results_lock = Lock()  # Thread-safe lock for flat_results
    
    # Filter PDFs that have matching JSONs before starting
    valid_pdfs = []
    for entry in pdfs:
        pdf_path = entry["pdf"]
        info = infer_docid_variant_from_pdf(pdf_path)
        if not info:
            skipped += 1
            continue
        
        # ICW has no variant, so we need to try both variants for JSON lookup
        if info['variant'] is None:
            # For ICW, try to find any variant JSON (prefer gibberish, then refusal_string)
            json_path = None
            for variant in ["gibberish", "refusal_string"]:
                key = f"{info['docid']}::{variant}"
                json_path = json_index.get(key)
                if json_path:
                    break
            if not json_path:
                skipped += 1
                continue
        else:
            key = f"{info['docid']}::{info['variant']}"
            json_path = json_index.get(key)
            if not json_path:
                skipped += 1
                continue
        
        valid_pdfs.append((entry, info, json_path))
    
    if not valid_pdfs:
        raise SystemExit("No valid PDFs with matching JSONs found to evaluate.")
    
    # Filter to 1 per domain-level if requested
    if args.one_per_domain_level:
        domain_level_map = {}
        for entry, info, json_path in valid_pdfs:
            # Extract domain and level from docid (e.g., "biology_graduate_doc_01")
            docid = info['docid']
            # Parse domain and level from docid
            parts = docid.split('_')
            if len(parts) >= 3:
                # Find where level starts (graduate, undergraduate, k-12)
                level_keywords = ['graduate', 'undergraduate', 'k-12']
                level_idx = None
                for i, part in enumerate(parts):
                    if part in level_keywords or (i > 0 and parts[i-1] == 'k' and part == '12'):
                        if part == '12':
                            level_idx = i - 1  # k-12 spans two parts
                        else:
                            level_idx = i
                        break
                if level_idx:
                    domain = '_'.join(parts[:level_idx])
                    if parts[level_idx] == 'k' and level_idx + 1 < len(parts) and parts[level_idx + 1] == '12':
                        level = 'k-12'
                    else:
                        level = parts[level_idx]
                    key = f"{domain}/{level}"
                    if key not in domain_level_map:
                        domain_level_map[key] = []
                    domain_level_map[key].append((entry, info, json_path))
        
        # Select 1 per combination (prefer doc_01, get all 9 methods/variants)
        filtered_pdfs = []
        for key in sorted(domain_level_map.keys()):
            pdf_list = sorted(domain_level_map[key], key=lambda x: x[1]['docid'])
            # Prefer doc_01
            doc01 = [p for p in pdf_list if "doc_01" in p[1]['docid']]
            if doc01:
                # Group by method and variant to get all 9 attacks
                method_variant_map = {}
                for entry, info, json_path in doc01:
                    method = info.get('method', 'unknown')
                    variant = info.get('variant', 'none')
                    mv_key = f"{variant}/{method}"
                    if mv_key not in method_variant_map:
                        method_variant_map[mv_key] = []
                    method_variant_map[mv_key].append((entry, info, json_path))
                # Take one from each method/variant combination (should be 9 total)
                for mv_key in sorted(method_variant_map.keys()):
                    filtered_pdfs.append(method_variant_map[mv_key][0])
            else:
                # If no doc_01, take first of each method/variant
                method_variant_map = {}
                for entry, info, json_path in pdf_list:
                    method = info.get('method', 'unknown')
                    variant = info.get('variant', 'none')
                    mv_key = f"{variant}/{method}"
                    if mv_key not in method_variant_map:
                        method_variant_map[mv_key] = []
                    method_variant_map[mv_key].append((entry, info, json_path))
                for mv_key in sorted(method_variant_map.keys()):
                    filtered_pdfs.append(method_variant_map[mv_key][0])
        
        original_count = len(valid_pdfs)
        valid_pdfs = filtered_pdfs
        print(f"Filtered to 1 per domain-level: {len(valid_pdfs)} PDFs (from {original_count} total)")
    
    print(f"Found {len(valid_pdfs)} valid PDFs to process (skipped {skipped} without matching JSONs)")
    
    # Worker function for parallel processing
    def process_pdf(entry_info_json):
        entry, info, json_path = entry_info_json
        pdf_path = entry["pdf"]
        local_errors = 0
        local_results = []
        
        # Build output directory path (ICW has no variant folder)
        if info["variant"]:
            doc_output_dir = output_dir / info["docid"] / info["variant"] / info["method"]
        else:
            doc_output_dir = output_dir / info["docid"] / info["method"]
        doc_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create a new collector instance for this thread (thread-safe)
            thread_collector = collector_class(config, model=args.model)
            thread_matcher = PreventionMatcher()
            
            # Collect responses
            response_data = thread_collector.collect_responses(pdf_path, json_path, doc_output_dir)
            
            # Load document data
            doc_data = json.loads(json_path.read_text(encoding="utf-8"))
            doc = Document.model_validate(doc_data)
            
            # Match responses
            detection_results: List[Dict[str, Any]] = []
            for response in response_data["responses"].values():
                q_num = response["question_number"]
                question = next((q for q in doc.questions if q.question_number == q_num), None)
                if not question:
                    continue
                match_result = thread_matcher.match_response(response, question)
                match_result["question_number"] = q_num
                match_result["question_type"] = response["question_type"]
                match_result["parsing_method"] = response.get("parsing_method")
                match_result["docid"] = info["docid"]
                match_result["variant"] = info["variant"]
                match_result["method"] = info["method"]
                detection_results.append(match_result)
                local_results.append(match_result)
            
            # Save detection results
            (doc_output_dir / "detection_results.json").write_text(
                json.dumps(detection_results, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            
            return {
                "success": True,
                "pdf_name": pdf_path.name,
                "results": local_results,
                "errors": 0,
                "info": info
            }
            
        except Exception as e:
            local_errors = 1
            error_msg = str(e)
            progress_logger.error(f"Error processing {pdf_path.name}: {error_msg}")
            
            # Check for rate limit errors
            is_rate_limit = "rate limit" in error_msg.lower() or "429" in error_msg
            return {
                "success": False,
                "pdf_name": pdf_path.name,
                "results": [],
                "errors": local_errors,
                "error": error_msg,
                "is_rate_limit": is_rate_limit,
                "info": info
            }
    
    # Process with ThreadPoolExecutor (5 workers) and tqdm progress bar
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        future_to_pdf = {executor.submit(process_pdf, pdf_info): pdf_info for pdf_info in valid_pdfs}
        
        # Process completed tasks with progress bar
        with tqdm(total=len(valid_pdfs), desc="Processing PDFs", unit="pdf", ncols=100, file=sys.stdout, disable=False) as pbar:
            for future in as_completed(future_to_pdf):
                pdf_info = future_to_pdf[future]
                entry, info, _ = pdf_info
                
                try:
                    result = future.result()
                    
                    # Thread-safe update of shared state
                    with results_lock:
                        flat_results.extend(result["results"])
                        errors += result["errors"]
                    
                    # Update progress bar
                    pbar.set_description(f"Processing {info['docid'][:30]}...")
                    pbar.set_postfix({
                        'variant': info['variant'],
                        'method': info['method'],
                        'errors': errors
                    })
                    
                    if result["success"]:
                        tqdm.write(f"  ✓ Completed {result['pdf_name']} ({len(result['results'])} results)")
                    else:
                        if result.get("is_rate_limit"):
                            tqdm.write(f"  ⚠ Rate limit hit for {result['pdf_name']}", file=sys.stderr)
                            sys.stderr.flush()
                            # Wait a bit for rate limits
                            time.sleep(10)
                        else:
                            tqdm.write(f"  ✗ Error processing {result['pdf_name']}: {result.get('error', 'Unknown')[:80]}", file=sys.stderr)
                            sys.stderr.flush()
                    
                except Exception as e:
                    with results_lock:
                        errors += 1
                    tqdm.write(f"  ✗ Exception processing {entry['pdf'].name}: {str(e)[:80]}", file=sys.stderr)
                    sys.stderr.flush()
                finally:
                    pbar.update(1)
                    
                # Small delay to avoid overwhelming the API
                if delay_between_requests > 0:
                    time.sleep(delay_between_requests)
    
    # Calculate final metrics
    if flat_results:
        print(f"\nCalculating prevention metrics for {len(flat_results)} question responses...")
        metrics = calculator.calculate_metrics(flat_results, output_dir=output_dir)
        print(f"\n✓ Prevention evaluation complete!")
        print(f"  Processed: {len(valid_pdfs)} PDFs")
        print(f"  Skipped: {skipped} PDFs")
        print(f"  Errors: {errors} PDFs")
        print(f"  Total questions: {len(flat_results)}")
        if metrics and "summary" in metrics:
            summary = metrics["summary"]
            print(f"\n  Prevention Success Rate: {summary.get('prevention_success_rate', 0):.2f}% (refusals)")
            print(f"  Prevention Failure Rate: {summary.get('prevention_failure_rate', 0):.2f}% (answered)")
            print(f"  Refusal Rate: {summary.get('refusal_rate', 0):.2f}%")
            if "by_variant" in metrics:
                print(f"\n  By Variant:")
                for variant, variant_metrics in metrics["by_variant"].items():
                    print(f"    {variant}: {variant_metrics.get('prevention_success_rate', 0):.2f}% success")
            if "by_method" in metrics:
                print(f"\n  By Method:")
                for method, method_metrics in metrics["by_method"].items():
                    print(f"    {method}: {method_metrics.get('prevention_success_rate', 0):.2f}% success")
    else:
        print(f"\n⚠ No results to calculate metrics (errors: {errors}, skipped: {skipped})")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

