"""Main test script for detection system - runs all 3 steps."""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.detection.response_collector import ResponseCollector
from src.detection.signature_matcher import SignatureMatcher
from src.detection.metrics_calculator import MetricsCalculator
from src.models.perturbation import Document

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_perturbed_pdfs(pdf_dir: Path, method_filter: str = None) -> List[Dict[str, Path]]:
    """
    Find all perturbed PDFs and their corresponding perturbation JSON files.
    
    Args:
        pdf_dir: Directory to search for PDFs
        method_filter: Optional method name to filter by (e.g., "dual_layer", "font_attack")
    
    Returns:
        List of dicts with 'pdf', 'json', 'domain', 'level', 'doc', and 'method' keys
    """
    pdfs = []
    
    # Search for PDFs in output_attacked_pdfs
    for pdf_file in pdf_dir.rglob("*.pdf"):
        # Skip compilation logs and intermediate files
        if "compile.log" in str(pdf_file):
            continue
        # Skip intermediate PDFs (keep final PDFs and font attack PDFs)
        if "final" not in str(pdf_file) and "font_attack" not in str(pdf_file):
            continue
        
        # Try to find corresponding perturbation JSON
        # PDF path: output_attacked_pdfs/<timestamp>/<domain>/<level>/<doc>/<method>/<doc>_<method>_final.pdf
        # JSON path: output_perturbation/<timestamp>/<domain>/<level>/<doc>/<doc>_perturbation.json
        
        pdf_parts = pdf_file.parts
        if "output_attacked_pdfs" not in pdf_parts:
            continue
        
        # Extract domain, level, doc, and method from PDF path
        try:
            pdf_idx = pdf_parts.index("output_attacked_pdfs")
            timestamp = pdf_parts[pdf_idx + 1]
            domain = pdf_parts[pdf_idx + 2]
            level = pdf_parts[pdf_idx + 3]
            doc_name = pdf_parts[pdf_idx + 4]
            method = pdf_parts[pdf_idx + 5] if pdf_idx + 5 < len(pdf_parts) else None
            
            # Filter by method if specified
            if method_filter and method != method_filter:
                continue
            
            # Try to find JSON path - first try with same timestamp, then search all timestamps
            json_path = None
            
            # Try 1: Same timestamp
            candidate = Path("output_perturbation") / timestamp / domain.lower() / level.lower() / doc_name / f"{doc_name}_perturbation.json"
            if candidate.exists():
                json_path = candidate
            else:
                # Try 2: Search all timestamps in output_perturbation
                perturbation_dir = Path("output_perturbation")
                if perturbation_dir.exists():
                    for ts_dir in perturbation_dir.iterdir():
                        if ts_dir.is_dir():
                            candidate = ts_dir / domain.lower() / level.lower() / doc_name / f"{doc_name}_perturbation.json"
                            if candidate.exists():
                                json_path = candidate
                                logger.info(f"Found JSON with different timestamp: {candidate}")
                                break
            
            if json_path and json_path.exists():
                pdfs.append({
                    "pdf": pdf_file,
                    "json": json_path,
                    "domain": domain,
                    "level": level,
                    "doc": doc_name,
                    "method": method
                })
            else:
                logger.warning(f"Could not find perturbation JSON for {pdf_file}")
        except (IndexError, ValueError) as e:
            logger.warning(f"Could not parse PDF path {pdf_file}: {e}")
            continue
    
    return pdfs


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test perturbed PDFs against GPT-5.2 and calculate detection metrics"
    )
    parser.add_argument(
        "--pdfs",
        type=str,
        default="output_attacked_pdfs",
        help="Directory containing perturbed PDFs (default: output_attacked_pdfs)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="Model to use (default: gpt-4o). For vision/PDF support, use gpt-4o or gpt-4-turbo)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of PDFs to test (for testing)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: output_detection/<timestamp>)"
    )
    parser.add_argument(
        "--method",
        type=str,
        default=None,
        choices=["icw", "dual_layer", "font_attack", "icw_dual_layer", "icw_font_attack"],
        help="Filter by attack method (default: all methods)"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = Config.from_yaml(args.config)
    
    # Set up output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output_detection") / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Output directory: {output_dir}")
    
    # Find PDFs
    pdf_dir = Path(args.pdfs)
    if not pdf_dir.exists():
        logger.error(f"PDF directory not found: {pdf_dir}")
        sys.exit(1)
    
    logger.info(f"Searching for PDFs in {pdf_dir}...")
    if args.method:
        logger.info(f"Filtering by attack method: {args.method}")
    pdf_files = find_perturbed_pdfs(pdf_dir, method_filter=args.method)
    
    if not pdf_files:
        if args.method:
            logger.error(f"No PDFs found with method '{args.method}' and corresponding perturbation JSONs")
        else:
            logger.error("No PDFs found with corresponding perturbation JSONs")
        sys.exit(1)
    
    if args.limit:
        pdf_files = pdf_files[:args.limit]
    
    logger.info(f"Found {len(pdf_files)} PDFs to test")
    
    # Initialize components
    collector = ResponseCollector(config, model=args.model)
    matcher = SignatureMatcher()
    calculator = MetricsCalculator()
    
    # Process each PDF
    all_detection_results = []
    
    for i, pdf_info in enumerate(pdf_files, 1):
        pdf_path = pdf_info["pdf"]
        json_path = pdf_info["json"]
        
        logger.info(f"\n[{i}/{len(pdf_files)}] Processing {pdf_path.name}")
        
        try:
            # Step 1: Collect responses
            logger.info("Step 1: Collecting responses...")
            doc_output_dir = output_dir / pdf_info["doc"]
            response_data = collector.collect_responses(pdf_path, json_path, doc_output_dir)
            
            # Load question data for matching
            with open(json_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            doc = Document.model_validate(doc_data)
            
            # Step 2: Match responses
            logger.info("Step 2: Matching responses to signatures...")
            detection_results = []
            
            for response in response_data["responses"].values():
                q_num = response["question_number"]
                # Find corresponding question
                question = next((q for q in doc.questions if q.question_number == q_num), None)
                
                if question:
                    match_result = matcher.match_response(response, question)
                    match_result["question_number"] = q_num
                    match_result["question_type"] = response["question_type"]
                    # Pass through parsing method from response
                    if "parsing_method" in response:
                        match_result["parsing_method"] = response["parsing_method"]
                    
                    # Add perturbation details if available
                    target_wrong_answer = response.get("target_wrong_answer")
                    if question.perturbations:
                        # Find perturbation that matches target_wrong_answer, or use first one
                        matching_perturbation = None
                        for pert in question.perturbations:
                            if pert.target_wrong_answer == target_wrong_answer:
                                matching_perturbation = pert
                                break
                        
                        # Use first perturbation if no exact match
                        if not matching_perturbation:
                            matching_perturbation = question.perturbations[0]
                        
                        # Add perturbation details to match result
                        match_result["perturbation"] = {
                            "original_substring": matching_perturbation.original_substring,
                            "replacement_substring": matching_perturbation.replacement_substring,
                            "start_pos": matching_perturbation.start_pos,
                            "end_pos": matching_perturbation.end_pos,
                            "reasoning": getattr(matching_perturbation, 'reasoning', None),
                            "verification": getattr(matching_perturbation, 'verification', None),
                        }
                    
                    detection_results.append(match_result)
                else:
                    logger.warning(f"Question {q_num} not found in document")
            
            # Save detection results for this document
            results_file = doc_output_dir / "detection_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "document_id": doc.docid,
                    "pdf_path": str(pdf_path),
                    "total_questions": len(detection_results),
                    "results": detection_results
                }, f, indent=2, ensure_ascii=False)
            
            all_detection_results.extend(detection_results)
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}", exc_info=True)
            continue
    
    # Step 3: Calculate overall metrics
    if all_detection_results:
        logger.info("\nStep 3: Calculating metrics...")
        metrics = calculator.calculate_metrics(all_detection_results, output_dir)
        calculator.generate_report(metrics, all_detection_results, output_dir)
        
        logger.info(f"\n✓ Detection testing complete!")
        logger.info(f"  Total questions tested: {len(all_detection_results)}")
        logger.info(f"  Overall Detection rate: {metrics['summary']['detection_rate']:.2f}%")
        logger.info(f"  Overall Refusal rate: {metrics['summary']['refusal_rate']:.2f}%")
        
        # Display parsing method metrics
        by_parsing = metrics.get("by_parsing_method", {})
        if by_parsing:
            logger.info(f"\n  Parsing Method Breakdown:")
            for method, method_metrics in sorted(by_parsing.items()):
                logger.info(f"    {method.upper()}:")
                logger.info(f"      Questions: {method_metrics['total_questions']}")
                logger.info(f"      Detection rate: {method_metrics['detection_rate']:.2f}%")
                logger.info(f"      Refusal rate: {method_metrics['refusal_rate']:.2f}%")
    else:
        logger.error("No detection results to calculate metrics")


if __name__ == "__main__":
    main()

