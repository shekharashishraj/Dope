"""Build prevention perturbation mappings (no LLM).

This generates many small, exact-match substitutions across stems + options.
We avoid spaces in replacements by operating at word-token granularity, so TeX
line-breaking remains stable (spaces remain untouched between replaced words).
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


_WORD_TOKEN_RE = re.compile(r"(?<!\\)[A-Za-z0-9]+")


def _stable_seed(*parts: str) -> int:
    h = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def _gibberish_token(length: int, rng: random.Random) -> str:
    if length <= 0:
        return ""
    return "".join(rng.choice(GIBBERISH_ALPHABET) for _ in range(length))


def _refusal_token(length: int, keyword_index: int) -> str:
    if length <= 0:
        return ""
    kw = REFUSAL_KEYWORDS[keyword_index % len(REFUSAL_KEYWORDS)]
    return (kw * ((length // len(kw)) + 1))[:length]


def build_prevention_mappings_for_text(
    *,
    text: str,
    question_number: int,
    docid: str,
    variant: str,
    refusal_string: str = DEFAULT_REFUSAL_STRING,
    keyword_start_index: int = 0,
) -> Tuple[List[Dict], int]:
    """Return a list of mapping dicts for a single text span and the next keyword index."""

    mappings: List[Dict] = []
    keyword_idx = keyword_start_index
    rng = random.Random(_stable_seed(docid, str(question_number), variant, text))

    for m in _WORD_TOKEN_RE.finditer(text):
        orig = m.group(0)
        if not orig:
            continue
        start_pos = m.start()
        end_pos = m.end()

        if variant == PREVENTION_VARIANT_GIBBERISH:
            repl = _gibberish_token(len(orig), rng)
        elif variant == PREVENTION_VARIANT_REFUSAL:
            # Word-level refusal semantics: cycle keywords (no spaces).
            repl = _refusal_token(len(orig), keyword_idx)
            keyword_idx += 1
        else:
            raise ValueError(f"Unknown prevention variant: {variant}")

        if not repl or repl == orig:
            continue

        mappings.append(
            {
                "question_index": question_number,
                "latex_stem_text": text,
                "original_substring": orig,
                "replacement_substring": repl,
                "start_pos": start_pos,
                "end_pos": end_pos,
                # For prevention we care about refusal; keep this field for schema completeness.
                "target_wrong_answer": "REFUSE",
                "reasoning": f"Prevention({variant}) token replacement to degrade model reading and encourage refusal.",
                # Extra fields (allowed by Pydantic models, extra='allow')
                "prevention_variant": variant,
            }
        )

    return mappings, keyword_idx


def build_prevention_mappings_for_question(
    *,
    q_spans: QuestionSpans,
    docid: str,
    variant: str,
    refusal_string: str = DEFAULT_REFUSAL_STRING,
) -> List[Dict]:
    """Build mappings for one question across stem + options (word-level)."""

    all_dicts: List[Dict] = []

    # Stem
    stem_dicts, next_idx = build_prevention_mappings_for_text(
        text=q_spans.stem_text,
        question_number=q_spans.question_number,
        docid=docid,
        variant=variant,
        refusal_string=refusal_string,
        keyword_start_index=0,
    )
    for d in stem_dicts:
        d["prevention_scope"] = "stem"
    all_dicts.extend(stem_dicts)

    # Options (if any)
    for opt_i, opt in enumerate(q_spans.options):
        opt_dicts, next_idx = build_prevention_mappings_for_text(
            text=opt.text,
            question_number=q_spans.question_number,
            docid=docid,
            variant=variant,
            refusal_string=refusal_string,
            keyword_start_index=next_idx,
        )
        for d in opt_dicts:
            d["prevention_scope"] = "option"
            d["option_index"] = opt_i
        all_dicts.extend(opt_dicts)

    return all_dicts

