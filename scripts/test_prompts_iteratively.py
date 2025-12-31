"""Iterative testing script for prompt versions."""
import argparse
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def find_latest_perturbation_folder(base_dir: Path = Path("output_perturbation")) -> Optional[Path]:
    """Find the latest perturbation folder by timestamp."""
    if not base_dir.exists():
        return None
    
    folders = [d for d in base_dir.iterdir() if d.is_dir() and d.name.isdigit()]
    if not folders:
        return None
    
    # Sort by timestamp (folder name format: YYYYMMDD_HHMMSS)
    folders.sort(key=lambda x: x.name, reverse=True)
    return folders[0]


def select_test_documents(perturbation_folder: Path, limit: int = 3) -> List[Path]:
    """
    Select test documents from perturbation folder.
    Prioritizes documents with TF questions.
    
    Args:
        perturbation_folder: Path to perturbation folder
        limit: Number of documents to select
    
    Returns:
        List of perturbation JSON file paths
    """
    json_files = []
    
    # Find all perturbation JSON files
    for json_file in perturbation_folder.rglob("*_perturbation.json"):
        json_files.append(json_file)
    
    # Prioritize documents with TF questions
    def count_tf_questions(json_path: Path) -> int:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            count = 0
            for q in data.get('questions', []):
                if q.get('question_type', '').upper() == 'TF':
                    count += 1
            return count
        except:
            return 0
    
    # Sort by TF question count (descending)
    json_files.sort(key=count_tf_questions, reverse=True)
    
    return json_files[:limit]


def backup_prompts(prompts_dir: Path, backup_dir: Path):
    """Backup current grouped batch prompts."""
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(parents=True)
    
    for prompt_file in prompts_dir.glob("*.py"):
        if prompt_file.name != "__init__.py":
            shutil.copy2(prompt_file, backup_dir / prompt_file.name)
    
    logger.info(f"Backed up prompts to {backup_dir}")


def restore_prompts(prompts_dir: Path, backup_dir: Path):
    """Restore prompts from backup."""
    if not backup_dir.exists():
        logger.warning(f"Backup directory does not exist: {backup_dir}")
        return
    
    for prompt_file in backup_dir.glob("*.py"):
        shutil.copy2(prompt_file, prompts_dir / prompt_file.name)
    
    logger.info(f"Restored prompts from {backup_dir}")


def copy_version_prompts(version_dir: Path, prompts_dir: Path):
    """Copy version prompts to active prompts directory."""
    for prompt_file in version_dir.glob("*.py"):
        if prompt_file.name != "__init__.py":
            # Map v2 function names to standard names
            if prompt_file.name == "tf_grouped_prompt.py":
                # Read and replace function names
                content = prompt_file.read_text(encoding='utf-8')
                # Replace format_grouped_tf_batch_v2 with format_grouped_tf_batch
                content = content.replace("format_grouped_tf_batch_v2", "format_grouped_tf_batch")
                content = content.replace("format_tf_question_entry_v2", "format_tf_question_entry")
                content = content.replace("TF_GROUPED_BATCH_TEMPLATE_V2", "TF_GROUPED_BATCH_TEMPLATE")
                (prompts_dir / prompt_file.name).write_text(content, encoding='utf-8')
            else:
                shutil.copy2(prompt_file, prompts_dir / prompt_file.name)
    
    logger.info(f"Copied version prompts from {version_dir} to {prompts_dir}")


def run_pdf_generation(
    perturbation_folder: Path,
    methods: List[str],
    limit: Optional[int] = None
) -> Path:
    """
    Run PDF generation for selected documents.
    
    Returns:
        Path to output directory with timestamp
    """
    cmd = [
        sys.executable, "-m", "src.pdf_generator",
        "--perturbation-folder", str(perturbation_folder),
        "--methods"
    ] + methods
    
    if limit:
        cmd.extend(["--limit", str(limit)])
    
    logger.info(f"Running PDF generation: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"PDF generation failed: {result.stderr}")
        raise RuntimeError(f"PDF generation failed: {result.stderr}")
    
    # Find the output directory (latest timestamp)
    output_base = Path("output_attacked_pdfs")
    if output_base.exists():
        folders = [d for d in output_base.iterdir() if d.is_dir()]
        if folders:
            folders.sort(key=lambda x: x.name, reverse=True)
            return folders[0]
    
    raise RuntimeError("Could not find output directory")


def run_detection(
    pdf_dir: Path,
    methods: List[str],
    model: str = "gpt-4o",
    limit: Optional[int] = None
) -> Path:
    """
    Run detection on generated PDFs.
    
    Returns:
        Path to detection output directory
    """
    # Run detection for each method separately or combined
    # For simplicity, run once with method filter if single method
    cmd = [
        sys.executable, "-m", "src.detection.test",
        "--pdfs", str(pdf_dir),
        "--model", model
    ]
    
    if len(methods) == 1:
        cmd.extend(["--method", methods[0]])
    
    if limit:
        cmd.extend(["--limit", str(limit)])
    
    logger.info(f"Running detection: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Detection failed: {result.stderr}")
        raise RuntimeError(f"Detection failed: {result.stderr}")
    
    # Find the output directory (latest timestamp)
    output_base = Path("output_detection")
    if output_base.exists():
        folders = [d for d in output_base.iterdir() if d.is_dir()]
        if folders:
            folders.sort(key=lambda x: x.name, reverse=True)
            return folders[0]
    
    raise RuntimeError("Could not find detection output directory")


def run_analyzer(detection_dir: Path) -> Path:
    """Run perturbation analyzer on detection results."""
    cmd = [
        sys.executable, "-m", "src.analysis.perturbation_analyzer",
        "--detection-dir", str(detection_dir)
    ]
    
    logger.info(f"Running analyzer: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Analyzer failed: {result.stderr}")
        raise RuntimeError(f"Analyzer failed: {result.stderr}")
    
    # Return path to analysis JSON
    analysis_file = detection_dir / "perturbation_analysis.json"
    if analysis_file.exists():
        return analysis_file
    
    raise RuntimeError("Analysis file not found")


def test_prompt_version(
    version_dir: Path,
    perturbation_folder: Path,
    methods: List[str],
    limit: int = 3,
    model: str = "gpt-4o",
    use_existing_perturbations: bool = True
) -> Dict[str, Any]:
    """
    Test a prompt version.
    
    Args:
        version_dir: Directory containing prompt version files
        perturbation_folder: Folder with perturbation JSONs
        methods: List of injection methods to test
        limit: Number of documents to test
        model: Model to use for detection
        use_existing_perturbations: If True, use existing perturbations; if False, regenerate
    
    Returns:
        Dict with test results and metrics
    """
    prompts_dir = project_root / "prompts" / "grouped_batch"
    backup_dir = project_root / "prompts" / "grouped_batch" / ".backup"
    
    results = {
        "version": version_dir.name,
        "timestamp": datetime.now().isoformat(),
        "methods": methods,
        "limit": limit,
        "model": model,
    }
    
    try:
        # 1. Backup current prompts
        backup_prompts(prompts_dir, backup_dir)
        
        # 2. Copy version prompts
        copy_version_prompts(version_dir, prompts_dir)
        
        # 3. Select test documents
        test_docs = select_test_documents(perturbation_folder, limit)
        logger.info(f"Selected {len(test_docs)} test documents")
        
        if not use_existing_perturbations:
            logger.info("Regenerating perturbations (not implemented - using existing)")
            # TODO: Implement perturbation regeneration if needed
        
        # 4. Generate PDFs
        logger.info("Generating attacked PDFs...")
        pdf_output_dir = run_pdf_generation(perturbation_folder, methods, limit=len(test_docs))
        results["pdf_output_dir"] = str(pdf_output_dir)
        
        # 5. Run detection
        logger.info("Running detection...")
        detection_output_dir = run_detection(pdf_output_dir, methods, model, limit=len(test_docs) * len(methods))
        results["detection_output_dir"] = str(detection_output_dir)
        
        # 6. Run analyzer
        logger.info("Running perturbation analyzer...")
        analysis_file = run_analyzer(detection_output_dir)
        results["analysis_file"] = str(analysis_file)
        
        # 7. Load metrics
        metrics_file = detection_output_dir / "detection_metrics.json"
        if metrics_file.exists():
            with open(metrics_file, 'r', encoding='utf-8') as f:
                results["metrics"] = json.load(f)
        
        # 8. Load analysis
        if analysis_file.exists():
            with open(analysis_file, 'r', encoding='utf-8') as f:
                results["analysis"] = json.load(f)
        
        logger.info(f"Test complete for version {version_dir.name}")
        
    except Exception as e:
        logger.error(f"Error testing version {version_dir.name}: {e}")
        results["error"] = str(e)
    
    finally:
        # 9. Restore prompts
        restore_prompts(prompts_dir, backup_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test prompt versions iteratively"
    )
    parser.add_argument(
        "--prompt-version",
        type=str,
        required=True,
        help="Path to prompt version directory (e.g., prompts/grouped_batch_v2)"
    )
    parser.add_argument(
        "--perturbation-folder",
        type=str,
        default=None,
        help="Path to perturbation folder (default: latest in output_perturbation)"
    )
    parser.add_argument(
        "--methods",
        type=str,
        nargs="+",
        default=["dual_layer", "font_attack"],
        choices=["icw", "dual_layer", "font_attack", "icw_dual_layer", "icw_font_attack"],
        help="Injection methods to test (default: dual_layer font_attack)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Number of documents to test (default: 3)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="Model to use for detection (default: gpt-4o)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file for results (default: test_results_<timestamp>.json)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    version_dir = Path(args.prompt_version)
    if not version_dir.exists():
        logger.error(f"Prompt version directory does not exist: {version_dir}")
        return
    
    # Determine perturbation folder
    if args.perturbation_folder:
        perturbation_folder = Path(args.perturbation_folder)
    else:
        perturbation_folder = find_latest_perturbation_folder()
        if not perturbation_folder:
            logger.error("Could not find perturbation folder")
            return
        logger.info(f"Using latest perturbation folder: {perturbation_folder}")
    
    if not perturbation_folder.exists():
        logger.error(f"Perturbation folder does not exist: {perturbation_folder}")
        return
    
    # Run test
    logger.info(f"Testing prompt version: {version_dir.name}")
    results = test_prompt_version(
        version_dir=version_dir,
        perturbation_folder=perturbation_folder,
        methods=args.methods,
        limit=args.limit,
        model=args.model
    )
    
    # Save results
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"test_results_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Test results saved to {output_path}")
    
    # Print summary
    if "metrics" in results:
        metrics = results["metrics"]
        summary = metrics.get("summary", {})
        logger.info(f"\n=== Test Summary ===")
        logger.info(f"Detection Rate: {summary.get('detection_rate', 0):.2f}%")
        logger.info(f"Total Questions: {summary.get('total_questions', 0)}")
        logger.info(f"Detected: {summary.get('detected', 0)}")
        logger.info(f"Not Detected: {summary.get('not_detected', 0)}")
        
        by_type = metrics.get("by_question_type", {})
        for qtype, stats in by_type.items():
            logger.info(f"\n{qtype}:")
            logger.info(f"  Detection Rate: {stats.get('detection_rate', 0):.2f}%")
            logger.info(f"  Total: {stats.get('total', 0)}")
            logger.info(f"  Detected: {stats.get('detected', 0)}")


if __name__ == "__main__":
    main()

