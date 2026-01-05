"""Prevention ICW injector (constant instruction template).

This is a prevention-mode parallel to `src/injection/icw_injector.py` but:
- does not depend on Pydantic Question/PerturbationMapping models
- injects a constant prevention string (template) once per question
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .latex_utils import escape_tex, insert_in_preamble
from ..constants import PREVENTION_ICW_PROMPT_TEMPLATE
from ..latex_struct_parser import extract_question_spans


_HIDDEN_MACRO = (
    "\\newcommand{\\hiddeninstruction}[1]{%\n"
    "  \\leavevmode\\begingroup\\color{white}\\fontsize{1pt}{1pt}\\selectfont\n"
    "  \\hbox to 0pt{\\smash{#1}\\hss}%\n"
    "  \\endgroup\n"
    "}\n"
)


def apply_prevention_icw(
    tex_content: str,
    *,
    question_numbers: List[int],
    prompt_template: str = PREVENTION_ICW_PROMPT_TEMPLATE,
) -> Tuple[str, Dict[str, Any]]:
    """Inject constant hidden prompts (one per question), placed before each question.

    We inject each instruction at the start of the corresponding question stem
    (right after \\item and any whitespace), rather than as a block at the end
    of the document.
    """

    mutated = tex_content

    if "\\usepackage{xcolor}" not in mutated:
        mutated = insert_in_preamble(mutated, "\\usepackage{xcolor}")
    if "\\hiddeninstruction" not in mutated:
        mutated = insert_in_preamble(mutated, _HIDDEN_MACRO)

    spans = extract_question_spans(mutated)
    insertions: List[Tuple[int, str]] = []
    injected = 0
    skipped = 0
    for qn in question_numbers:
        q_spans = spans.get(qn)
        if not q_spans:
            skipped += 1
            continue
        instruction = prompt_template.format(question_number=str(qn))
        snippet = f"\\hiddeninstruction{{{escape_tex(instruction)}}}"
        insertions.append((q_spans.stem_start, snippet))
        injected += 1

    # Apply from back to front to preserve indices
    insertions.sort(key=lambda x: x[0], reverse=True)
    for pos, snippet in insertions:
        mutated = mutated[:pos] + snippet + mutated[pos:]

    return mutated, {
        "method": "prevention_icw",
        "instructions_count": injected,
        "instructions_skipped": skipped,
        "prompt_template": prompt_template,
    }

