"""Shared LaTeX helpers for prevention injectors (copied/simplified from src/injection)."""

from __future__ import annotations

import re


def insert_in_preamble(tex: str, snippet: str) -> str:
    """Insert snippet before \\begin{document} (or at start if missing)."""

    match = re.search(r"\\begin\{document\}", tex)
    if not match:
        return snippet + "\n" + tex
    insert_at = match.start()
    return tex[:insert_at] + snippet + "\n" + tex[insert_at:]


def escape_tex(value: str) -> str:
    """Escape LaTeX special characters in plain text."""

    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "#": r"\#",
        "%": r"\%",
        "&": r"\&",
        "_": r"\_",
        "^": r"\^{}",
        "~": r"\~{}",
    }
    return "".join(replacements.get(ch, ch) for ch in value)

