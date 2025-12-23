#!/usr/bin/env python3
"""
Master pipeline script to run all steps: Normalize, Render, and Apply Attacks.
Runs the complete pipeline with a single command.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # python-dotenv not installed, skip .env loading


def setup_logging(log_dir="logs"):
    """Setup logging to file with timestamp."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"00_pipeline_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file


def extract_subject_from_path(input_file):
    """Extract subject name from input file path.
    
    Expected path pattern: Input/<Subject>/<file>.json
    Returns the subject name (e.g., 'Maths', 'Science')
    """
    input_path = Path(input_file)
    # Get the parent directory name (should be the subject)
    # Input/Maths/file.json -> Maths
    parent_dir = input_path.parent.name
    
    # If parent is 'Input', try to get from the path components
    if parent_dir.lower() == 'input' or parent_dir == '':
        # Try to find Input/<Subject> pattern
        parts = input_path.parts
        try:
            input_idx = [p.lower() for p in parts].index('input')
            if input_idx + 1 < len(parts):
                return parts[input_idx + 1]
        except ValueError:
            pass
        # Fallback: use 'default' if we can't determine
        logging.warning(f"Could not extract subject from path {input_file}, using 'default'")
        return 'default'
    
    return parent_dir


def run_command(cmd, description, step_num, total_steps):
    """Run a command and handle errors."""
    logging.info("=" * 80)
    logging.info(f"Step {step_num}/{total_steps}: {description}")
    logging.info(f"Command: {' '.join(cmd)}")
    logging.info("=" * 80)
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,  # Show output in real-time
            text=True
        )
        logging.info(f"[OK] Step {step_num}/{total_steps}: {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"[FAIL] Step {step_num}/{total_steps}: {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logging.error(f"[ERROR] Step {step_num}/{total_steps}: {description}: {e}")
        return False


def run_pipeline(input_json, registry_file="attacks/registry.json", data_dir="data", 
                 baseline_dir="out/baseline", attacked_dir="out/attacked",
                 generate_perturbations=False, api_key=None, model="gpt-4o", k=3):
    """Run the complete pipeline: Normalize -> [Generate Perturbations] -> Render -> Apply Attacks."""
    
    log_file = setup_logging()
    logging.info("=" * 80)
    logging.info("Starting Complete Pipeline")
    logging.info(f"Input JSON: {input_json}")
    logging.info(f"Generate perturbations: {generate_perturbations}")
    if generate_perturbations:
        logging.info(f"API model: {model}, k={k}")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 80)
    
    # Validate input file
    if not os.path.exists(input_json):
        logging.error(f"Input JSON file not found: {input_json}")
        sys.exit(1)
    
    # Validate registry file
    if not os.path.exists(registry_file):
        logging.error(f"Registry file not found: {registry_file}")
        sys.exit(1)
    
    # Extract subject name
    subject_name = extract_subject_from_path(input_json)
    logging.info(f"Detected subject: {subject_name}")
    logging.info("")
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Step 1: Normalize JSON
    normalized_json = os.path.join(data_dir, "exam_content.json")
    normalize_cmd = [
        sys.executable,
        "scripts/01_normalize_json.py",
        input_json,
        normalized_json
    ]
    
    total_steps = 3  # Base steps: Normalize, Render, Apply Traditional Attacks
    if generate_perturbations:
        total_steps = 6  # Add: Generate Perturbations, CSS ::before, Image/Canvas
    
    if not run_command(normalize_cmd, "Normalizing JSON", 1, total_steps):
        logging.error("Pipeline failed at normalization step")
        sys.exit(1)
    
    logging.info("")
    
    # Step 2: Render Baseline HTML
    render_cmd = [
        sys.executable,
        "scripts/02_render_exam.py",
        normalized_json,
        baseline_dir,
        subject_name  # Pass the extracted subject name
    ]
    
    if not run_command(render_cmd, "Rendering Baseline HTML", 2, total_steps):
        logging.error("Pipeline failed at rendering step")
        sys.exit(1)
    
    # Verify baseline HTML was created
    baseline_html = os.path.join(baseline_dir, subject_name, "exam.html")
    if not os.path.exists(baseline_html):
        logging.error(f"Baseline HTML not found at expected path: {baseline_html}")
        logging.error("Pipeline failed - baseline HTML was not generated")
        sys.exit(1)
    
    logging.info("")
    
    # Step 2.5: Generate Perturbations (optional, after HTML rendering)
    perturbed_json = os.path.join(data_dir, "exam_content_perturbed.json")
    if generate_perturbations:
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logging.error("OpenAI API key required for perturbation generation. "
                         "Provide via --api-key or set OPENAI_API_KEY environment variable")
            sys.exit(1)
        
        perturb_cmd = [
            sys.executable,
            "scripts/01b_generate_perturbations.py",
            normalized_json,
            perturbed_json,
            "--baseline-html", baseline_html,
            "--api-key", api_key,
            "--model", model,
            "--k", str(k)
        ]
        
        # Step 2.5: Generate Perturbations (after HTML rendering, uses HTML text)
        if not run_command(perturb_cmd, "Generating Perturbations", 3, total_steps):
            logging.error("Pipeline failed at perturbation generation step")
            sys.exit(1)
        
        # Verify perturbed JSON was created
        if not os.path.exists(perturbed_json):
            logging.error(f"Perturbed JSON not found at expected path: {perturbed_json}")
            logging.error("Pipeline failed - perturbed JSON was not generated")
            sys.exit(1)
        
        logging.info("")
    
    # Step 3 or 4: Apply Attacks (existing hidden-text attacks)
    # Step number depends on whether perturbations were generated
    attack_step = 4 if generate_perturbations else 3
    apply_attacks_cmd = [
        sys.executable,
        "scripts/03_apply_attacks.py",
        baseline_html,
        registry_file,
        attacked_dir
    ]
    
    if not run_command(apply_attacks_cmd, "Applying Traditional Attacks", attack_step, total_steps):
        logging.error("Pipeline failed at attack application step")
        sys.exit(1)
    
    logging.info("")
    
    # Step 4: Apply CSS ::before Attack (if perturbations exist)
    if generate_perturbations and os.path.exists(perturbed_json):
        css_before_cmd = [
            sys.executable,
            "scripts/03b_apply_css_before_attack.py",
            baseline_html,
            perturbed_json,
            attacked_dir,
            subject_name
        ]
        
        if not run_command(css_before_cmd, "Applying CSS ::before Attack", 5, total_steps):
            logging.warning("CSS ::before attack failed, continuing with pipeline")
        else:
            logging.info("")
    
    # Step 5: Apply Image/Canvas Attack (if perturbations exist)
    if generate_perturbations and os.path.exists(perturbed_json):
        image_canvas_cmd = [
            sys.executable,
            "scripts/03c_apply_image_canvas_attack.py",
            baseline_html,
            perturbed_json,
            attacked_dir,
            subject_name
        ]
        
        if not run_command(image_canvas_cmd, "Applying Image/Canvas Attack", 6, total_steps):
            logging.warning("Image/Canvas attack failed, continuing with pipeline")
        else:
            logging.info("")
    
    # Summary
    logging.info("")
    logging.info("=" * 80)
    logging.info("Pipeline completed successfully!")
    logging.info(f"Subject: {subject_name}")
    logging.info(f"Baseline HTML: {baseline_html}")
    logging.info(f"Attacked HTML files: {os.path.join(attacked_dir, subject_name)}")
    if generate_perturbations:
        logging.info(f"Perturbed JSON: {perturbed_json}")
    logging.info("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run complete exam processing pipeline")
    parser.add_argument("input_json", help="Path to input JSON file")
    parser.add_argument("--registry", default="attacks/registry.json", 
                       help="Path to attack registry file (default: attacks/registry.json)")
    parser.add_argument("--generate-perturbations", action="store_true",
                       help="Generate perturbations using LLM API")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)")
    parser.add_argument("--k", type=int, default=3, 
                       help="Number of perturbations per question (default: 3)")
    
    args = parser.parse_args()
    
    # Get API key from argument or environment
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    
    run_pipeline(
        input_json=args.input_json,
        registry_file=args.registry,
        generate_perturbations=args.generate_perturbations,
        api_key=api_key,
        model=args.model,
        k=args.k
    )

