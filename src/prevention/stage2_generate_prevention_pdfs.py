"""Stage 2 (prevention): generate attacked PDFs from prevention perturbation JSONs."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import List

import pytz
from tqdm import tqdm

from .injection.prevention_orchestrator import generate_prevention_dual_layer_pdf
from .injection.prevention_orchestrator import generate_prevention_font_attack_pdf
from .injection.prevention_orchestrator import generate_prevention_icw_pdf
from .injection.prevention_orchestrator import generate_prevention_icw_dual_layer_pdf
from .injection.prevention_orchestrator import generate_prevention_icw_font_attack_pdf


def _tz_now_str(tz_name: str = "America/Denver") -> str:
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).strftime("%Y%m%d_%H%M%S")


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_prevention_jsons(prevention_root: Path) -> List[Path]:
    return sorted(prevention_root.rglob("*_prevention_perturbation_*.json"))

def _output_base_for_pdf(
    *,
    output_root: Path,
    run_ts: str,
    doc: dict,
    method: str,
    variant: str | None,
) -> Path:
    """Match detection run layout: <ts>/<domain>/<Level>/<doc>/<method>/..."""

    domain = str(doc.get("domain") or "unknown")
    level = str(doc.get("academic_level") or "Unknown")
    docid = str(doc.get("docid") or "unknown_doc")

    method_dir = output_root / run_ts / domain / level / docid / method
    method_dir.mkdir(parents=True, exist_ok=True)

    if method == "icw":
        return method_dir / f"{docid}_icw"
    if variant:
        return method_dir / f"{docid}_{variant}_{method}"
    return method_dir / f"{docid}_{method}"


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
        choices=["icw", "dual_layer", "font_attack", "icw_dual_layer", "icw_font_attack"],
        default="dual_layer",
        help="Method to run",
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

    # For ICW: run once per docid (avoid duplicates across variants)
    if args.method == "icw":
        representative: dict[str, Path] = {}
        for pjson in jsons:
            name = pjson.name
            if "_prevention_perturbation_" not in name:
                continue
            docid = name.split("_prevention_perturbation_")[0]
            representative.setdefault(docid, pjson)
        items = list(representative.items())
        with tqdm(total=len(items), desc=f"Stage2 {args.method}", unit="pdf") as pbar:
            for docid, pjson in items:
                doc = json.loads(pjson.read_text(encoding="utf-8"))
                output_base = _output_base_for_pdf(
                    output_root=output_root,
                    run_ts=run_ts,
                    doc=doc,
                    method="icw",
                    variant=None,
                )
                generate_prevention_icw_pdf(
                    prevention_json_path=pjson,
                    output_base=output_base,
                    compile_pdf=not args.no_pdf,
                )
                pbar.set_postfix(doc=docid)
                pbar.update(1)
        print(f"Done. Outputs under: {output_root}/{run_ts}/")
        return 0

    with tqdm(total=len(jsons), desc=f"Stage2 {args.method}", unit="pdf") as pbar:
        for pjson in jsons:
            doc = json.loads(pjson.read_text(encoding="utf-8"))
            variant = (doc.get("prevention") or {}).get("variant")
            output_base = _output_base_for_pdf(
                output_root=output_root,
                run_ts=run_ts,
                doc=doc,
                method=args.method,
                variant=variant,
            )

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
            elif args.method == "icw_dual_layer":
                generate_prevention_icw_dual_layer_pdf(
                    prevention_json_path=pjson,
                    output_base=output_base,
                    compile_pdf=not args.no_pdf,
                )
            elif args.method == "icw_font_attack":
                generate_prevention_icw_font_attack_pdf(
                    prevention_json_path=pjson,
                    output_base=output_base,
                    font_cache_dir=font_cache_dir,
                    compile_pdf=not args.no_pdf,
                )
            else:
                raise ValueError(f"Unknown method: {args.method}")

            pbar.set_postfix(doc=str(doc.get("docid")), variant=str(variant))
            pbar.update(1)

    print(f"Done. Outputs under: {output_root}/{run_ts}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

