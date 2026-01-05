"""Build a reusable font cache for prevention font-attack.

Goal: precompute fonts keyed by (hidden_char, visual_char) so Stage 2 can do
quick lookups instead of generating fonts per PDF.

Important design choice:
- We will NOT attack whitespace. Spaces/newlines are left as-is, so we don't need
  fonts mapping to/from whitespace.
- We also avoid LaTeX control sequences; visual chars are extracted from the
  *visible* text in LaTeX (best-effort heuristic).
"""

from __future__ import annotations

import argparse
import json
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import contextlib
import io
from tqdm import tqdm

from ..injection.font_builder import FontBuilder, FontBuildError
from .constants import DEFAULT_REFUSAL_STRING, GIBBERISH_ALPHABET


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _discover_input_jsons(input_root: Path) -> List[Path]:
    return sorted(input_root.rglob("JSON_output/*_doc_*.json"))


def _resolve_latex_path(repo_root: Path, latex_path_str: str) -> Path:
    norm = latex_path_str.replace("\\", "/")
    p = Path(norm)
    if p.is_absolute():
        return p
    return (repo_root / p).resolve()


def _iter_visible_chars_from_latex(latex: str) -> Iterable[str]:
    """Best-effort extraction of visible characters from LaTeX source.

    Heuristic:
    - Skip LaTeX control sequences (backslash + letters/@)
    - Skip brace characters { }
    - Skip newlines and tabs
    - Yield remaining characters
    """

    i = 0
    while i < len(latex):
        ch = latex[i]
        if ch == "\\":
            # Skip control sequence name
            i += 1
            while i < len(latex) and (latex[i].isalpha() or latex[i] in ["@", "*"]):
                i += 1
            continue
        if ch in ["{", "}"]:
            i += 1
            continue
        if ch in ["\n", "\r", "\t"]:
            i += 1
            continue
        yield ch
        i += 1


def _default_hidden_charset(refusal_string: str) -> Set[str]:
    # Hidden chars come from two variants:
    # - gibberish (lowercase)
    # - refusal_string (lowercase letters + punctuation in the refusal string)
    chars = set(GIBBERISH_ALPHABET)
    for ch in refusal_string:
        if ch in ["\n", "\r", "\t"]:
            continue
        chars.add(ch)
    # Include spaces as well: we explicitly want to change whitespace signature.
    # (We still exclude hard newlines/tabs.)
    return {c for c in chars if c not in ["\n", "\r", "\t"]}


def _default_visual_charset() -> Set[str]:
    # Start with printable ASCII including space.
    base = set(string.printable)
    base = {c for c in base if len(c) == 1 and 32 <= ord(c) < 127}  # includes space
    # Exclude backslash and braces (not visually rendered directly)
    base.discard("\\")
    base.discard("{")
    base.discard("}")
    return base


def scan_visual_charset(
    latex_paths: List[Path],
    *,
    restrict_to_ascii: bool = True,
) -> Set[str]:
    visual: Set[str] = set()
    for p in latex_paths:
        try:
            latex = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            latex = p.read_text(encoding="latin-1")
        for ch in _iter_visible_chars_from_latex(latex):
            # Include spaces (but not newlines/tabs)
            if ch in ["\n", "\r", "\t"]:
                continue
            if restrict_to_ascii and ord(ch) >= 127:
                continue
            visual.add(ch)
    # Avoid these explicitly
    visual.discard("\\")
    visual.discard("{")
    visual.discard("}")
    return visual


def build_cache(
    *,
    base_font_path: Path,
    output_dir: Path,
    hidden_chars: Set[str],
    visual_chars: Set[str],
    dry_run: bool = False,
) -> Dict[str, int]:
    """Build the font cache; returns build statistics."""

    # In dry-run mode we only write metadata; do not require a valid base font.
    builder = None if dry_run else FontBuilder(base_font_path)

    attempted = 0
    built = 0
    skipped = 0

    output_dir.mkdir(parents=True, exist_ok=True)

    total = len(hidden_chars) * len(visual_chars)
    with tqdm(total=total, desc="Font cache build", unit="font") as pbar:
        for hidden in sorted(hidden_chars):
            for visual in sorted(visual_chars):
                attempted += 1
                # Cache key filename-safe
                key = f"h{ord(hidden):04x}_v{ord(visual):04x}.ttf"
                out_path = output_dir / key
                if out_path.exists():
                    skipped += 1
                    pbar.update(1)
                    continue
                if dry_run:
                    skipped += 1
                    pbar.update(1)
                    continue
                try:
                    assert builder is not None
                    # FontBuilder is very chatty; suppress stdout for progress readability.
                    with contextlib.redirect_stdout(io.StringIO()):
                        builder.build_font(hidden_char=hidden, visual_text=visual, output_path=out_path)
                    built += 1
                except FontBuildError:
                    skipped += 1
                pbar.set_postfix(built=built, skipped=skipped)
                pbar.update(1)

    meta = {
        "base_font": str(base_font_path),
        "hidden_chars": sorted(hidden_chars),
        "visual_chars": sorted(visual_chars),
    }
    (output_dir / "cache_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    return {"attempted": attempted, "built": built, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build prevention font cache (hidden_char -> visual_char)")
    parser.add_argument("--input-root", type=str, default="output", help="Input root containing JSON_output (default: output)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of docs for scan/build")
    parser.add_argument("--output-dir", type=str, default="output_prevention_font_cache", help="Where to write cache fonts/metadata")
    parser.add_argument(
        "--base-font",
        type=str,
        default=None,
        help="Base font to clone (default: try repo Roboto, else system Arial.ttf)",
    )
    parser.add_argument("--refusal-string", type=str, default=DEFAULT_REFUSAL_STRING, help="Refusal string (defines hidden charset)")
    parser.add_argument("--dry-run", action="store_true", help="Scan and write metadata only (do not build fonts)")
    parser.add_argument("--no-ascii-restrict", action="store_true", help="Allow non-ASCII visual chars if present")

    args = parser.parse_args()

    repo_root = _resolve_repo_root()
    input_root = (repo_root / args.input_root).resolve()

    jsons = _discover_input_jsons(input_root)
    if args.limit:
        jsons = jsons[: args.limit]

    latex_paths: List[Path] = []
    for jp in jsons:
        doc = json.loads(jp.read_text(encoding="utf-8"))
        latex_file = (doc.get("file_paths") or {}).get("latex_file")
        if not latex_file:
            continue
        latex_paths.append(_resolve_latex_path(repo_root, latex_file))

    restrict_ascii = not args.no_ascii_restrict
    visual_chars = scan_visual_charset(latex_paths, restrict_to_ascii=restrict_ascii)
    # Also include a conservative default set so cache is stable across small scans
    visual_chars |= _default_visual_charset()

    hidden_chars = _default_hidden_charset(args.refusal_string)

    # Choose a default base font if not provided.
    if args.base_font:
        base_font_path = (repo_root / args.base_font).resolve() if not Path(args.base_font).is_absolute() else Path(args.base_font)
    else:
        repo_roboto = (repo_root / "resources/fonts/Roboto-Regular.ttf").resolve()
        # If it's a Git LFS pointer, it will be tiny ASCII text.
        is_lfs_pointer = False
        if repo_roboto.exists() and repo_roboto.stat().st_size < 2048:
            head = repo_roboto.read_text(encoding="utf-8", errors="ignore")
            if head.startswith("version https://git-lfs.github.com/spec/v1"):
                is_lfs_pointer = True
        if repo_roboto.exists() and not is_lfs_pointer:
            base_font_path = repo_roboto
        else:
            base_font_path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = build_cache(
        base_font_path=base_font_path,
        output_dir=output_dir,
        hidden_chars=hidden_chars,
        visual_chars=visual_chars,
        dry_run=args.dry_run,
    )

    print(
        f"Font cache at {output_dir}\n"
        f"Hidden chars: {len(hidden_chars)}  Visual chars: {len(visual_chars)}\n"
        f"Attempted: {stats['attempted']}  Built: {stats['built']}  Skipped: {stats['skipped']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

