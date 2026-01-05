"""Stage 2 (prevention): generate attacked PDFs from prevention perturbation JSONs."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import List

import pytz

from .injection.prevention_orchestrator import generate_prevention_dual_layer_pdf
from .injection.prevention_orchestrator import generate_prevention_font_attack_pdf


def _tz_now_str(tz_name: str = "America/Denver") -> str:
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).strftime("%Y%m%d_%H%M%S")


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_prevention_jsons(prevention_root: Path) -> List[Path]:
    return sorted(prevention_root.rglob("*_prevention_perturbation_*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 2 (prevention): generate attacked PDFs")
    parser.add_argument(
        "--prevention-folder",
        type=str,
        required=True,
        help="Folder containing prevention perturbation JSONs (searches recursively)",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default="output_prevention_attacked_pdfs",
        help="Base output directory (default: output_prevention_attacked_pdfs)",
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["dual_layer", "font_attack"],
        default="dual_layer",
        help="Method to run (for now: dual_layer only)",
    )
    parser.add_argument(
        "--font-cache-dir",
        type=str,
        default="output_prevention_font_cache",
        help="Font cache directory for font_attack (default: output_prevention_font_cache)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of docs")
    parser.add_argument("--timezone", type=str, default="America/Denver", help="Timezone for timestamps")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF compilation (LaTeX only)")

    args = parser.parse_args()

    repo_root = _resolve_repo_root()
    prevention_folder = Path(args.prevention_folder).resolve()
    output_root = (repo_root / args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    font_cache_dir = (repo_root / args.font_cache_dir).resolve()

    run_ts = _tz_now_str(args.timezone)

    jsons = find_prevention_jsons(prevention_folder)
    if args.limit:
        jsons = jsons[: args.limit]

    for pjson in jsons:
        # Keep a mirrored layout under output root
        rel = pjson.relative_to(prevention_folder)
        # .../<doc>/<file>.json -> output base: .../<doc>/<method>/<stem>_<method>
        doc_dir = output_root / run_ts / rel.parent
        method_dir = doc_dir / args.method
        method_dir.mkdir(parents=True, exist_ok=True)
        base_name = pjson.stem.replace("_prevention_perturbation_", "_")
        output_base = method_dir / f"{base_name}_{args.method}"

        if args.method == "dual_layer":
            generate_prevention_dual_layer_pdf(
                prevention_json_path=pjson,
                output_base=output_base,
                compile_pdf=not args.no_pdf,
            )
        elif args.method == "font_attack":
            generate_prevention_font_attack_pdf(
                prevention_json_path=pjson,
                output_base=output_base,
                font_cache_dir=font_cache_dir,
                compile_pdf=not args.no_pdf,
            )

    print(f"Done. Outputs under: {output_root}/{run_ts}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

