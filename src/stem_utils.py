"""Utilities for normalizing question stem text for LaTeX/JSON consistency."""
import re

# Leading "Q<n>." pattern (e.g. "Q1.", "Q2. ", "Q 10. ")
_Q_STEM_PREFIX = re.compile(r"^\s*Q\s*\d+\s*\.\s*", re.IGNORECASE)


def normalize_latex_stem(text: str) -> str:
    """
    Strip a leading "Q<n>." label from stem text so it matches LaTeX item body.

    LaTeX uses \\begin{enumerate}[label=Q\\arabic*.] so "Q1." is rendered by the
    label; the item body is just the stem. This ensures latex_stem_text equals
    what appears after \\item in the .tex file.

    Args:
        text: Raw stem text (may start with "Q1. ", "Q2.", etc.).

    Returns:
        Stem with leading Q<n>. removed and trimmed; original if no match.
    """
    if not text or not isinstance(text, str):
        return text or ""
    stripped = _Q_STEM_PREFIX.sub("", text, count=1)
    return stripped.strip() if stripped != text else text.strip()
