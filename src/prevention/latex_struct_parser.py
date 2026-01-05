"""Parse LaTeX documents to locate question stem and option text spans.

Goal: extract *raw* substrings (with original whitespace/newlines) so we can
create exact-match perturbation mappings for prevention.

Assumptions (matches current dataset LaTeX structure):
- Questions live inside \\begin{enumerate} ... \\end{enumerate}
- Each question is a top-level \\item at enumerate depth 1
- MCQ options (if present) live in a nested \\begin{enumerate} ... \\end{enumerate}
  inside that question item, with \\item entries for options.
- Question numbering uses \\setcounter{enumi}{N} across sections.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional, Tuple, Dict


@dataclass(frozen=True)
class OptionSpan:
    """Raw option text span for a single option item (without the leading \\item)."""

    start: int
    end: int
    text: str


@dataclass(frozen=True)
class QuestionSpans:
    """Raw spans for a question: stem span plus optional option spans."""

    question_number: int
    stem_start: int
    stem_end: int
    stem_text: str
    options: List[OptionSpan]


_SECTION_SPLIT_RE = re.compile(r"\\section\*\{[^}]*\}")
_SETCOUNTER_RE = re.compile(r"\\setcounter\{enumi\}\{(\d+)\}")


def _depth_before(content: str, pos: int) -> int:
    """Enumerate nesting depth before a position, using begin/end counts."""

    before = content[:pos]
    return before.count("\\begin{enumerate}") - before.count("\\end{enumerate}")


def _find_matching_end_enumerate(content: str, begin_pos: int) -> Optional[int]:
    """Find the matching \\end{enumerate} for a \\begin{enumerate} at begin_pos.

    Returns the index of the start of the matching \\end{enumerate}, or None.
    """

    depth = 0
    i = begin_pos
    while i < len(content):
        next_begin = content.find("\\begin{enumerate}", i)
        next_end = content.find("\\end{enumerate}", i)
        if next_end == -1:
            return None
        if next_begin != -1 and next_begin < next_end:
            depth += 1
            i = next_begin + len("\\begin{enumerate}")
            continue
        depth -= 1
        if depth == 0:
            return next_end
        i = next_end + len("\\end{enumerate}")
    return None


def _extract_option_spans(option_block: str, block_abs_start: int) -> List[OptionSpan]:
    """Extract per-option spans within a nested enumerate block."""

    spans: List[OptionSpan] = []
    option_items = list(re.finditer(r"\\item", option_block))
    if not option_items:
        return spans

    for idx, m in enumerate(option_items):
        item_pos = m.start()
        # Depth inside option_block: we want items at depth==1 relative to the nested enumerate
        if _depth_before(option_block, item_pos) != 1:
            continue

        start = item_pos + len("\\item")
        while start < len(option_block) and option_block[start].isspace():
            start += 1

        end = len(option_block)
        for nxt in option_items:
            if nxt.start() <= item_pos:
                continue
            if _depth_before(option_block, nxt.start()) == 1:
                end = nxt.start()
                break

        # Stop at end enumerate if that comes first
        end_enum = option_block.find("\\end{enumerate}", start)
        if end_enum != -1:
            end = min(end, end_enum)

        text = option_block[start:end]
        abs_start = block_abs_start + start
        abs_end = block_abs_start + end
        spans.append(OptionSpan(start=abs_start, end=abs_end, text=text))

    return spans


def extract_question_spans(latex: str) -> Dict[int, QuestionSpans]:
    """Extract raw stem + option spans for all questions in a LaTeX document.

    Returns:
      Dict[question_number, QuestionSpans]
    """

    spans_by_q: Dict[int, QuestionSpans] = {}

    # Split by sections to respect \\setcounter resets.
    # Keep it simple: find section boundaries and iterate over chunks.
    section_starts = [m.start() for m in _SECTION_SPLIT_RE.finditer(latex)]
    if not section_starts:
        section_starts = [0]
    section_starts.append(len(latex))

    current_question = 1
    for i in range(len(section_starts) - 1):
        sec_start = section_starts[i]
        sec_end = section_starts[i + 1]
        section_content = latex[sec_start:sec_end]

        counter_match = _SETCOUNTER_RE.search(section_content)
        if counter_match:
            current_question = int(counter_match.group(1)) + 1

        all_items = list(re.finditer(r"\\item", section_content))
        for item_idx, item_match in enumerate(all_items):
            item_pos = item_match.start()
            if _depth_before(section_content, item_pos) != 1:
                continue

            # Item start: after \\item and whitespace
            start = item_pos + len("\\item")
            while start < len(section_content) and section_content[start].isspace():
                start += 1

            # Item end: next \\item at depth 1, or end of section_content
            end = len(section_content)
            for nxt in all_items:
                if nxt.start() <= item_pos:
                    continue
                if _depth_before(section_content, nxt.start()) == 1:
                    end = nxt.start()
                    break

            # Also cap at the matching \\end{enumerate} for the *current* top-level enumerate
            # to avoid leaking trailing LaTeX (e.g., \\end{enumerate}, \\vfill, \\end{document})
            top_enum_end = section_content.find("\\end{enumerate}", start)
            if top_enum_end != -1 and top_enum_end < end:
                end = top_enum_end

            item_text = section_content[start:end]

            # Identify nested enumerate for MCQ options (first nested enumerate in the item)
            nested_begin_rel = item_text.find("\\begin{enumerate}")
            stem_text = item_text if nested_begin_rel == -1 else item_text[:nested_begin_rel]
            stem_abs_start = sec_start + start
            stem_abs_end = stem_abs_start + len(stem_text)

            options: List[OptionSpan] = []
            if nested_begin_rel != -1:
                nested_begin_abs = sec_start + start + nested_begin_rel
                nested_end_abs = _find_matching_end_enumerate(latex, nested_begin_abs)
                if nested_end_abs is not None:
                    option_block = latex[nested_begin_abs:nested_end_abs + len("\\end{enumerate}")]
                    options = _extract_option_spans(option_block, nested_begin_abs)

            spans_by_q[current_question] = QuestionSpans(
                question_number=current_question,
                stem_start=stem_abs_start,
                stem_end=stem_abs_end,
                stem_text=latex[stem_abs_start:stem_abs_end],
                options=options,
            )
            current_question += 1

    return spans_by_q

