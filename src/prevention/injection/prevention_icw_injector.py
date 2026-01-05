"""Prevention ICW injector (constant instruction template).

This is a prevention-mode parallel to `src/injection/icw_injector.py` but:
- does not depend on Pydantic Question/PerturbationMapping models
- injects a constant prevention string (template) once per question
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .latex_utils import escape_tex, insert_in_preamble
from ..constants import PREVENTION_ICW_PROMPT_TEMPLATE


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
    """Inject constant hidden prompts (one per question)."""

    mutated = tex_content

    if "\\usepackage{xcolor}" not in mutated:
        mutated = insert_in_preamble(mutated, "\\usepackage{xcolor}")
    if "\\hiddeninstruction" not in mutated:
        mutated = insert_in_preamble(mutated, _HIDDEN_MACRO)

    lines = ["% --- PREVENTION ICW hidden prompts begin ---"]
    for qn in question_numbers:
        instruction = prompt_template.format(question_number=str(qn))
        lines.append(f"\\hiddeninstruction{{{escape_tex(instruction)}}}")
    lines.append("% --- PREVENTION ICW hidden prompts end ---")
    block = "\n".join(lines) + "\n"

    if "% --- PREVENTION ICW hidden prompts begin ---" in mutated:
        start = mutated.index("% --- PREVENTION ICW hidden prompts begin ---")
        end_marker = "% --- PREVENTION ICW hidden prompts end ---"
        end = mutated.index(end_marker, start) + len(end_marker)
        mutated = mutated[:start] + block + mutated[end:]
    else:
        end_doc = mutated.rfind("\\end{document}")
        if end_doc == -1:
            mutated = mutated + "\n" + block
        else:
            mutated = mutated[:end_doc] + block + mutated[end_doc:]

    return mutated, {
        "method": "prevention_icw",
        "instructions_count": len(question_numbers),
        "prompt_template": prompt_template,
    }

