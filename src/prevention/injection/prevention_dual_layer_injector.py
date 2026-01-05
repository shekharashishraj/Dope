"""Prevention dual-layer injector.

Applies ALL provided perturbation mappings across stems + options by replacing each
`original_substring` with a `\\duallayerbox{original}{replacement}` wrapper, leaving
spaces intact so line-breaking remains stable.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from .latex_utils import escape_tex, insert_in_preamble


DUAL_LAYER_MACRO_DEFINITION = r"""
% --- latex-dual-layer macros (auto-generated) ---
\newlength{\dlboxwidth}
\newlength{\dlboxheight}
\newlength{\dlboxdepth}
\newcommand{\duallayerbox}[2]{%
  \begingroup
  \settowidth{\dlboxwidth}{\strut #1}%
  \settoheight{\dlboxheight}{\strut #1}%
  \settodepth{\dlboxdepth}{\strut #1}%
  \ifdim\dlboxwidth=0pt
    \settowidth{\dlboxwidth}{#2}%
  \fi
  \raisebox{0pt}[\dlboxheight][\dlboxdepth]{%
    \makebox[\dlboxwidth][l]{\resizebox{\dlboxwidth}{!}{\strut #2}}%
  }%
  \endgroup
}
% --- end latex-dual-layer macros ---
""".strip()


PACKAGE_DEPENDENCIES = ("graphicx", "calc", "xcolor")


def _ensure_packages(tex: str) -> str:
    for package in PACKAGE_DEPENDENCIES:
        if f"\\usepackage{{{package}}}" not in tex:
            tex = insert_in_preamble(tex, f"\\usepackage{{{package}}}")
    return tex


def _find_span(tex: str, span_text: str) -> Tuple[int, int] | None:
    """Find span_text inside tex, with a couple normalization fallbacks."""

    idx = tex.find(span_text)
    if idx != -1:
        return idx, idx + len(span_text)

    # Normalize whitespace (best-effort) and search
    norm_span = re.sub(r"\s+", " ", span_text.strip())
    norm_tex = re.sub(r"\s+", " ", tex)
    nidx = norm_tex.find(norm_span)
    if nidx != -1:
        # We cannot reliably map indices back; caller should fallback to substring search.
        return None

    return None


def apply_prevention_dual_layer(
    tex_content: str,
    perturbations: List[Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    """Apply dual-layer wrappers for all mappings."""

    mutated = _ensure_packages(tex_content)
    if "\\duallayerbox" not in mutated:
        mutated = insert_in_preamble(mutated, DUAL_LAYER_MACRO_DEFINITION)

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
            # Be strict: never apply outside of the intended stem span.
            skipped += 1
            continue
        else:
            span_start, span_end = span
            # Prefer positional slice if consistent
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

        # Add an explicit break opportunity after each box. Without this, TeX often
        # can't break lines (each \\duallayerbox is effectively an unbreakable unit),
        # causing overfull \\hbox and stem text running into options.
        wrapped = f"\\duallayerbox{{{escape_tex(orig)}}}{{{escape_tex(repl)}}}\\allowbreak"
        meta = {
            "question_index": p.get("question_index"),
            "scope": p.get("prevention_scope"),
            "original": orig,
            "replacement": repl,
            "position": (abs_start, abs_end),
        }
        replacements.append((abs_start, abs_end, wrapped, meta))

    # Deduplicate exact replacements
    seen = set()
    unique: List[Tuple[int, int, str, Dict[str, Any]]] = []
    for s, e, r, m in replacements:
        key = (s, e, r)
        if key in seen:
            continue
        seen.add(key)
        unique.append((s, e, r, m))

    # Apply in reverse order
    unique.sort(key=lambda x: x[0], reverse=True)
    metas: List[Dict[str, Any]] = []
    for s, e, r, m in unique:
        mutated = mutated[:s] + r + mutated[e:]
        metas.append(m)

    return mutated, {
        "method": "prevention_dual_layer",
        "replacements_applied": len(unique),
        "replacements_skipped": skipped,
        "replacements": list(reversed(metas)),  # preserve forward order for readability
    }

