"""Prevention font-attack injector (cached).

This injector replaces spans inside the *stem* with hidden text (replacement),
but uses cached custom fonts so the PDF *visually* shows the original text.

Key properties:
- Strictly applies within `latex_stem_text` spans (no global fallback).
- Per-character mapping: hidden_char -> visual_char.
- Uses a precomputed cache of fonts: `h{hidden_code}_v{visual_code}.ttf`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .latex_utils import insert_in_preamble


def _find_span(tex: str, span_text: str) -> Tuple[int, int] | None:
    idx = tex.find(span_text)
    if idx != -1:
        return idx, idx + len(span_text)
    return None


def _latex_char(hex_codepoint: int) -> str:
    """Emit a character safely in LaTeX via \\char"XXXX.

    This is critical for spaces and punctuation, which can be swallowed or
    re-tokenized if emitted literally.
    """

    return f'\\char\"{hex_codepoint:04X}'


def _font_filename(hidden: str, visual: str) -> str:
    return f"h{ord(hidden):04x}_v{ord(visual):04x}.ttf"

def _cmd_suffix_base26(n: int) -> str:
    """Convert integer to a letter-only suffix (a, b, ..., z, aa, ab, ...)."""

    if n < 0:
        raise ValueError("n must be non-negative")
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    s = ""
    n = n + 1  # 1-indexed for bijective base-26
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = alphabet[rem] + s
    return s


@dataclass
class FontAttackResult:
    modified_tex: str
    font_files_needed: List[str]  # relative filenames under cache dir
    metadata: Dict[str, Any]


def apply_prevention_font_attack(
    tex_content: str,
    perturbations: List[Dict[str, Any]],
    *,
    font_cache_dir: Path,
) -> FontAttackResult:
    mutated = tex_content

    if "\\usepackage{fontspec}" not in mutated:
        mutated = insert_in_preamble(mutated, "\\usepackage{fontspec}")

    # Registry: (hidden_char, visual_char) -> command name + font filename stem
    pair_to_cmd: Dict[Tuple[str, str], str] = {}
    pair_to_file: Dict[Tuple[str, str], str] = {}
    cmd_decls: List[str] = []

    replacements: List[Tuple[int, int, str, Dict[str, Any]]] = []
    skipped = 0

    for p in perturbations:
        span_text = p.get("latex_stem_text") or ""
        orig = p.get("original_substring") or ""
        repl = p.get("replacement_substring") or ""
        start_pos = p.get("start_pos")
        end_pos = p.get("end_pos")

        if not span_text or not orig or not repl:
            skipped += 1
            continue

        span = _find_span(mutated, span_text)
        if not span:
            skipped += 1
            continue

        span_start, span_end = span

        abs_start = None
        abs_end = None
        if isinstance(start_pos, int) and isinstance(end_pos, int) and 0 <= start_pos < end_pos <= len(span_text):
            abs_start = span_start + start_pos
            abs_end = span_start + end_pos
            if mutated[abs_start:abs_end] != orig:
                abs_start = None
                abs_end = None

        if abs_start is None:
            local = mutated[span_start:span_end]
            li = local.find(orig)
            if li == -1:
                skipped += 1
                continue
            abs_start = span_start + li
            abs_end = abs_start + len(orig)

        # Build replacement latex: per-character font switch to render as original
        # Ensure equal length (expected by prevention Stage 1).
        if len(orig) != len(repl):
            # Best-effort: truncate to min
            n = min(len(orig), len(repl))
            orig_eff = orig[:n]
            repl_eff = repl[:n]
        else:
            orig_eff = orig
            repl_eff = repl

        pieces: List[str] = []
        for hidden_ch, visual_ch in zip(repl_eff, orig_eff):
            # Do not attempt to map LaTeX control sequences: if the visual char
            # is a backslash, skip (we don't want to render commands).
            if visual_ch == "\\":
                pieces.append(_latex_char(ord(hidden_ch)))
                continue

            key = (hidden_ch, visual_ch)
            if key not in pair_to_cmd:
                cmd = f"\\pfa{_cmd_suffix_base26(len(pair_to_cmd))}"
                pair_to_cmd[key] = cmd
                fname = _font_filename(hidden_ch, visual_ch)
                pair_to_file[key] = fname
                stem = Path(fname).stem
                # fontspec: load by stem with Extension=.ttf from fonts/
                cmd_decls.append(f"\\newfontfamily{cmd}{{{stem}}}[Path=fonts/,Extension=.ttf]")

            cmd = pair_to_cmd[key]
            pieces.append(f"{{{cmd} {_latex_char(ord(hidden_ch))}}}")

        latex_replacement = "".join(pieces)
        replacements.append(
            (
                abs_start,
                abs_end,
                latex_replacement,
                {
                    "question_index": p.get("question_index"),
                    "original": orig_eff,
                    "replacement": repl_eff,
                    "position": (abs_start, abs_end),
                },
            )
        )

    # Apply replacements in reverse order
    replacements.sort(key=lambda x: x[0], reverse=True)
    applied_meta: List[Dict[str, Any]] = []
    for s, e, r, m in replacements:
        mutated = mutated[:s] + r + mutated[e:]
        applied_meta.append(m)

    # Insert font declarations into preamble once
    if cmd_decls:
        mutated = insert_in_preamble(mutated, "\n".join(cmd_decls))

    # Determine which font files we need to copy from cache
    needed = sorted(set(pair_to_file.values()))

    return FontAttackResult(
        modified_tex=mutated,
        font_files_needed=needed,
        metadata={
            "method": "prevention_font_attack",
            "replacements_applied": len(replacements),
            "replacements_skipped": skipped,
            "fonts_needed": len(needed),
            "replacements": list(reversed(applied_meta)),
        },
    )

