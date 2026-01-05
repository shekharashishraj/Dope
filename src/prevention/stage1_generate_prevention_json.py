"""Stage 1 (prevention): generate prevention perturbation JSONs from existing input docs.

This does NOT call any LLMs. It parses the paired LaTeX and produces many small
word-level substitutions across stems + options, in two variants:
- gibberish
- refusal_string
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pytz
from tqdm import tqdm

from .constants import (
    PREVENTION_VARIANT_GIBBERISH,
    PREVENTION_VARIANT_REFUSAL,
    DEFAULT_REFUSAL_STRING,
)
from .latex_struct_parser import extract_question_spans
from .mapping_builder import build_prevention_mappings_for_question


def _tz_now_str(tz_name: str = "America/Denver") -> str:
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).strftime("%Y%m%d_%H%M%S")


def _resolve_repo_root() -> Path:
    # src/prevention/... -> repo root = 3 parents up
    return Path(__file__).resolve().parents[2]


def _resolve_latex_path(repo_root: Path, latex_path_str: str) -> Path:
    # JSON stores windows separators often
    norm = latex_path_str.replace("\\", "/")
    p = Path(norm)
    if p.is_absolute():
        return p
    return (repo_root / p).resolve()


def _discover_input_jsons(input_root: Path) -> List[Path]:
    return sorted(input_root.rglob("JSON_output/*_doc_*.json"))


def _output_dir_for_doc(
    *,
    base_output: Path,
    run_timestamp: str,
    doc: Dict,
) -> Path:
    subject = str(doc.get("domain") or "unknown").lower()
    level = str(doc.get("academic_level") or "unknown").lower()
    docid = str(doc.get("docid") or "unknown_doc")
    return base_output / run_timestamp / subject / level / docid


def generate_prevention_for_doc(
    *,
    json_path: Path,
    variant: str,
    run_timestamp: str,
    base_output: Path,
    refusal_string: str,
    tz_name: str,
) -> Path:
    repo_root = _resolve_repo_root()

    doc = json.loads(json_path.read_text(encoding="utf-8"))

    file_paths = doc.get("file_paths") or {}
    latex_file = file_paths.get("latex_file")
    if not latex_file:
        raise ValueError(f"Missing file_paths.latex_file in {json_path}")

    latex_path = _resolve_latex_path(repo_root, latex_file)
    latex = latex_path.read_text(encoding="utf-8")
    spans = extract_question_spans(latex)

    # Build perturbations per question
    for q in doc.get("questions", []):
        q_num = q.get("question_number")
        if not isinstance(q_num, int):
            q["perturbations"] = []
            continue
        q_spans = spans.get(q_num)
        if not q_spans:
            q["perturbations"] = []
            continue
        q["perturbations"] = build_prevention_mappings_for_question(
            q_spans=q_spans,
            docid=str(doc.get("docid") or json_path.stem),
            variant=variant,
            refusal_string=refusal_string,
        )

    out_dir = _output_dir_for_doc(base_output=base_output, run_timestamp=run_timestamp, doc=doc)
    out_dir.mkdir(parents=True, exist_ok=True)

    docid = str(doc.get("docid") or json_path.stem)
    out_name = f"{docid}_prevention_perturbation_{variant}.json"
    out_path = out_dir / out_name

    # Keep all extra fields; include prevention metadata at top-level via extra keys
    out_payload = doc
    out_payload["prevention"] = {
        "variant": variant,
        "refusal_string": refusal_string,
        "generated_at": datetime.now(pytz.timezone(tz_name)).isoformat(),
        "source_json": str(json_path),
        "source_latex": str(latex_path),
    }

    out_path.write_text(json.dumps(out_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 1 (prevention): generate prevention perturbation JSONs")
    parser.add_argument(
        "--input-root",
        type=str,
        default="output",
        help="Root input directory containing subject/level/JSON_output (default: output)",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default="output_prevention_perturbation",
        help="Base output directory (default: output_prevention_perturbation)",
    )
    parser.add_argument(
        "--variant",
        type=str,
        choices=[PREVENTION_VARIANT_GIBBERISH, PREVENTION_VARIANT_REFUSAL, "both"],
        default="both",
        help="Which prevention variant(s) to generate",
    )
    parser.add_argument(
        "--input-json",
        type=str,
        default=None,
        help="Optional: path to a single input JSON doc (overrides discovery)",
    )
    parser.add_argument(
        "--docid",
        type=str,
        default=None,
        help="Optional: only process docs whose filename contains this docid (e.g., biology_graduate_doc_03)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of docs (for testing)")
    parser.add_argument(
        "--refusal-string",
        type=str,
        default=DEFAULT_REFUSAL_STRING,
        help="Refusal string used for refusal_string variant",
    )
    parser.add_argument("--timezone", type=str, default="America/Denver", help="Timezone for timestamps")

    args = parser.parse_args()

    repo_root = _resolve_repo_root()
    input_root = (repo_root / args.input_root).resolve()
    output_root = (repo_root / args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    run_timestamp = _tz_now_str(args.timezone)

    if args.input_json:
        inputs = [Path(args.input_json).resolve()]
    else:
        inputs = _discover_input_jsons(input_root)

    if args.docid:
        inputs = [p for p in inputs if args.docid in p.name]
    if args.limit:
        inputs = inputs[: args.limit]

    variants: List[str]
    if args.variant == "both":
        variants = [PREVENTION_VARIANT_GIBBERISH, PREVENTION_VARIANT_REFUSAL]
    else:
        variants = [args.variant]

    created: List[Path] = []
    total = len(inputs) * len(variants)
    with tqdm(total=total, desc="Stage1 prevention JSONs", unit="json") as pbar:
        for json_path in inputs:
            for variant in variants:
                created.append(
                    generate_prevention_for_doc(
                        json_path=json_path,
                        variant=variant,
                        run_timestamp=run_timestamp,
                        base_output=output_root,
                        refusal_string=args.refusal_string,
                        tz_name=args.timezone,
                    )
                )
                pbar.set_postfix(doc=json_path.stem, variant=variant)
                pbar.update(1)

    print(f"Generated {len(created)} prevention JSON(s) in {output_root}/{run_timestamp}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

