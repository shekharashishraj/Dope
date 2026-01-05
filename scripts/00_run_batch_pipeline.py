#!/usr/bin/env python3
"""
Batch pipeline script to process multiple random JSON files.

Usage:
    python scripts/00_run_batch_pipeline.py --count 50 [--generate-perturbations] [--model gpt-4o] [--k 3] [--seed 42]
"""

import argparse
import logging
import os
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # Optional dependency; safe to continue without it
    pass


def setup_logging(log_dir: str = "logs") -> str:
    """Setup logging to file with timestamp."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"00_batch_pipeline_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_file


def find_all_json_files(input_dir: str = "Input") -> List[Tuple[str, str, str]]:
    """
    Find all JSON files in the Input directory structure.

    Returns:
        List of tuples: (json_path, domain, education_level)
    """
    json_files: List[Tuple[str, str, str]] = []
    input_path = Path(input_dir)

    if not input_path.exists():
        logging.error("Input directory not found: %s", input_dir)
        return json_files

    for domain_dir in input_path.iterdir():
        if not domain_dir.is_dir():
            continue

        domain_name = domain_dir.name

        # Skip non-domain directories
        if domain_name in {"pdf_documents", "__pycache__"}:
            continue

        for level_dir in domain_dir.iterdir():
            if not level_dir.is_dir():
                continue

            education_level = level_dir.name
            json_output_dir = level_dir / "JSON_output"

            if not json_output_dir.exists():
                continue

            for json_file in json_output_dir.glob("*.json"):
                json_files.append((str(json_file), domain_name, education_level))

    return json_files


def select_random_files(
    all_files: List[Tuple[str, str, str]], count: int
) -> List[Tuple[str, str, str]]:
    """
    Randomly select N files from the list.
    """
    if count >= len(all_files):
        logging.warning(
            "Requested %d files but only %d available. Using all files.",
            count,
            len(all_files),
        )
        return all_files

    selected = random.sample(all_files, count)

    # Log distribution for visibility
    domain_counts: Dict[str, int] = {}
    for _, domain, level in selected:
        key = f"{domain}/{level}"
        domain_counts[key] = domain_counts.get(key, 0) + 1

    logging.info("Selected %d files across domains:", len(selected))
    for domain_key, cnt in sorted(domain_counts.items()):
        logging.info("  - %s: %d files", domain_key, cnt)

    return selected


def run_single_pipeline(
    json_file: str,
    domain: str,
    level: str,
    generate_perturbations: bool,
    api_key: str,
    model: str,
    k: int,
) -> bool:
    """Run pipeline for a single JSON file."""
    logging.info("=" * 80)
    logging.info("Processing: %s/%s", domain, level)
    logging.info("File: %s", json_file)
    logging.info("=" * 80)

    cmd = [
        sys.executable,
        "scripts/00_run_pipeline.py",
        json_file,
        "--registry",
        "attacks/registry.json",
        "--domain",
        domain,
        "--education-level",
        level,
    ]

    if generate_perturbations:
        cmd.append("--generate-perturbations")
        if api_key:
            cmd.extend(["--api-key", api_key])
        cmd.extend(["--model", model, "--k", str(k)])

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=False,  # stream output
            text=True,
        )
        logging.info("[SUCCESS] %s/%s", domain, level)
        return True
    except subprocess.CalledProcessError as e:
        logging.error("[FAILED] %s/%s exit code %s", domain, level, e.returncode)
        return False
    except Exception as e:
        logging.error("[ERROR] %s/%s: %s", domain, level, e)
        return False


def run_batch_pipeline(
    count: int,
    generate_perturbations: bool = False,
    api_key: str = None,
    model: str = "gpt-4o",
    k: int = 3,
) -> None:
    """Run pipeline on multiple random JSON files."""
    log_file = setup_logging()

    logging.info("=" * 80)
    logging.info("BATCH PIPELINE STARTED")
    logging.info("Target count: %d files", count)
    logging.info("Generate perturbations: %s", generate_perturbations)
    if generate_perturbations:
        logging.info("Model: %s, k=%d", model, k)
    logging.info("Log file: %s", log_file)
    logging.info("=" * 80)

    logging.info("Scanning for JSON files...")
    all_files = find_all_json_files()
    logging.info("Found %d total JSON files", len(all_files))

    if not all_files:
        logging.error("No JSON files found in Input directory")
        sys.exit(1)

    selected_files = select_random_files(all_files, count)
    logging.info("Selected %d files for processing\n", len(selected_files))

    results = {"success": [], "failed": []}

    for idx, (json_file, domain, level) in enumerate(selected_files, start=1):
        logging.info("\n%s", "=" * 80)
        logging.info("PROCESSING FILE %d/%d", idx, len(selected_files))
        logging.info("%s\n", "=" * 80)

        success = run_single_pipeline(
            json_file,
            domain,
            level,
            generate_perturbations,
            api_key,
            model,
            k,
        )

        if success:
            results["success"].append((json_file, domain, level))
        else:
            results["failed"].append((json_file, domain, level))

    logging.info("\n%s", "=" * 80)
    logging.info("BATCH PIPELINE COMPLETED")
    logging.info("=" * 80)
    logging.info("Total files processed: %d", len(selected_files))
    logging.info("Successful: %d", len(results["success"]))
    logging.info("Failed: %d", len(results["failed"]))

    if results["failed"]:
        logging.info("\nFailed files:")
        for json_file, domain, level in results["failed"]:
            logging.info("  - %s/%s: %s", domain, level, json_file)

    success_rate = (
        len(results["success"]) / len(selected_files) * 100 if selected_files else 0
    )
    logging.info("Success rate: %.1f%%", success_rate)
    logging.info("=" * 80)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run pipeline on multiple random JSON files from various domains"
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        required=True,
        help="Number of random JSON files to process (max 100 recommended)",
    )
    parser.add_argument(
        "--generate-perturbations",
        action="store_true",
        help="Generate perturbations using LLM API",
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Number of perturbations per question (default: 3)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility (optional)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.count <= 0:
        print("Error: --count must be positive")
        sys.exit(1)

    if args.count > 100:
        print("Warning: Processing more than 100 files may take a long time")
        response = input("Continue? (y/n): ").strip().lower()
        if response != "y":
            sys.exit(0)

    if args.seed is not None:
        random.seed(args.seed)
        logging.info("Using random seed: %s", args.seed)

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")

    if args.generate_perturbations and not api_key:
        print("Error: --generate-perturbations requires API key")
        print("Provide via --api-key or set OPENAI_API_KEY environment variable")
        sys.exit(1)

    run_batch_pipeline(
        count=args.count,
        generate_perturbations=args.generate_perturbations,
        api_key=api_key,
        model=args.model,
        k=args.k,
    )

