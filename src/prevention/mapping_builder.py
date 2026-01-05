"""Build prevention perturbation mappings (no LLM).

Updated prevention strategy:
- Target ONLY question stems (NOT options).
- Do NOT preserve the original whitespace/space structure: replacements may
  introduce/remove spaces within replaced spans.

To keep LaTeX compilation stable, we:
- avoid modifying LaTeX commands (segments containing backslashes/braces)
- avoid generating mapping spans that include newlines
"""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass
from typing import Dict, List, Iterable, Optional, Tuple

from .constants import (
    PREVENTION_VARIANT_GIBBERISH,
    PREVENTION_VARIANT_REFUSAL,
    DEFAULT_REFUSAL_STRING,
    REFUSAL_KEYWORDS,
    GIBBERISH_ALPHABET,
)
from .latex_struct_parser import QuestionSpans


_SAFE_CHUNK_CHAR_RE = re.compile(r"[^\n\\{}]+")  # avoid newline, backslash, braces


def _stable_seed(*parts: str) -> int:
    h = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def _gibberish_chunk(length: int, rng: random.Random) -> str:
    if length <= 0:
        return ""
    # Allow spaces, but not newlines. This intentionally breaks original space structure.
    alphabet = GIBBERISH_ALPHABET + "     "
    s = "".join(rng.choice(alphabet) for _ in range(length))
    # Ensure we don't return all-whitespace
    if s.strip() == "":
        s = "".join(rng.choice(GIBBERISH_ALPHABET) for _ in range(length))
    return s


def _refusal_chunk(length: int, offset: int, refusal_string: str) -> str:
    if length <= 0:
        return ""
    # Use the configured refusal string, repeat+slice with a shifting offset so
    # space pattern changes across chunks.
    base = (refusal_string + " ") * ((length // (len(refusal_string) + 1)) + 3)
    start = offset % max(len(base), 1)
    s = (base[start:] + base)[:length]
    # No newlines
    return s.replace("\n", " ")


def build_prevention_mappings_for_text(
    *,
    text: str,
    question_number: int,
    docid: str,
    variant: str,
    refusal_string: str = DEFAULT_REFUSAL_STRING,
    chunk_size: int = 24,
) -> Tuple[List[Dict], int]:
    """Return mapping dicts for a single text span (stem only).

    We generate mappings over *safe* chunks that:
    - do not include newlines
    - do not include LaTeX command delimiters (\\, {, })
    """

    mappings: List[Dict] = []
    rng = random.Random(_stable_seed(docid, str(question_number), variant, text))
    offset = _stable_seed(docid, str(question_number), variant) % 10_000

    for safe_match in _SAFE_CHUNK_CHAR_RE.finditer(text):
        safe_segment = safe_match.group(0)
        if not safe_segment:
            continue

        seg_start = safe_match.start()
        seg_end = safe_match.end()

        # Chunk within the safe segment.
        i = 0
        while i < len(safe_segment):
            take = min(chunk_size, len(safe_segment) - i)
            orig = safe_segment[i : i + take]
            if not orig or orig.strip() == "":
                i += take
                continue

            start_pos = seg_start + i
            end_pos = start_pos + len(orig)

            if variant == PREVENTION_VARIANT_GIBBERISH:
                repl = _gibberish_chunk(len(orig), rng)
            elif variant == PREVENTION_VARIANT_REFUSAL:
                repl = _refusal_chunk(len(orig), offset, refusal_string)
                offset += len(orig)
            else:
                raise ValueError(f"Unknown prevention variant: {variant}")

            if not repl or repl == orig:
                i += take
                continue

            mappings.append(
                {
                    "question_index": question_number,
                    "latex_stem_text": text,
                    "original_substring": orig,
                    "replacement_substring": repl,
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "target_wrong_answer": "REFUSE",
                    "reasoning": f"Prevention({variant}) chunk replacement to degrade readability and encourage refusal.",
                    "prevention_variant": variant,
                    "prevention_scope": "stem",
                }
            )
            i += take

    return mappings, offset


def build_prevention_mappings_for_question(
    *,
    q_spans: QuestionSpans,
    docid: str,
    variant: str,
    refusal_string: str = DEFAULT_REFUSAL_STRING,
) -> List[Dict]:
    """Build mappings for one question (stem only)."""

    stem_dicts, _ = build_prevention_mappings_for_text(
        text=q_spans.stem_text,
        question_number=q_spans.question_number,
        docid=docid,
        variant=variant,
        refusal_string=refusal_string,
    )
    return stem_dicts

