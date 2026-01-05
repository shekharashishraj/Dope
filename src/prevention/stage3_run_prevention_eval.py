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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add repo root to sys.path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# These imports require the full Python deps (`pip install -r requirements.txt`).
try:
    from src.config import Config
    from src.detection.response_collector import ResponseCollector
    from src.detection.signature_matcher import SignatureMatcher
    from src.detection.metrics_calculator import MetricsCalculator
    from src.models.perturbation import Document
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
    stem = pdf_path.stem
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
    parser.add_argument("--model", type=str, default="gpt-4o", help="Model to use for response collection (vision/PDF)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of PDFs to evaluate")
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

    collector = ResponseCollector(config, model=args.model)
    matcher = SignatureMatcher()
    calculator = MetricsCalculator()

    flat_results: List[Dict[str, Any]] = []
    for i, entry in enumerate(pdfs, 1):
        pdf_path = entry["pdf"]
        info = infer_docid_variant_from_pdf(pdf_path)
        if not info:
            print(f"[skip] Could not infer docid/variant from {pdf_path.name}")
            continue

        key = f"{info['docid']}::{info['variant']}"
        json_path = json_index.get(key)
        if not json_path:
            print(f"[skip] No prevention JSON found for {key} (pdf={pdf_path})")
            continue

        doc_output_dir = output_dir / info["docid"] / info["variant"] / info["method"]
        doc_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[{i}/{len(pdfs)}] Collecting responses for {pdf_path.name}")
        response_data = collector.collect_responses(pdf_path, json_path, doc_output_dir)

        doc_data = json.loads(json_path.read_text(encoding="utf-8"))
        doc = Document.model_validate(doc_data)

        detection_results: List[Dict[str, Any]] = []
        for response in response_data["responses"].values():
            q_num = response["question_number"]
            question = next((q for q in doc.questions if q.question_number == q_num), None)
            if not question:
                continue
            match_result = matcher.match_response(response, question)
            match_result["question_number"] = q_num
            match_result["question_type"] = response["question_type"]
            match_result["parsing_method"] = response.get("parsing_method")
            match_result["docid"] = info["docid"]
            match_result["variant"] = info["variant"]
            match_result["method"] = info["method"]
            detection_results.append(match_result)
            flat_results.append(match_result)

        (doc_output_dir / "detection_results.json").write_text(
            json.dumps(detection_results, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    metrics = calculator.calculate_metrics(flat_results, output_dir=output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

