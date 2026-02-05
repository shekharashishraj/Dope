"""Build LaTeX source from extracted Document JSON (for dual-layer / inject pipeline)."""
import json
import logging
import re
from pathlib import Path
from typing import List, Optional

from .models.perturbation import Document, FilePaths

logger = logging.getLogger(__name__)

# Characters that have special meaning in LaTeX and must be escaped in text
_LATEX_SPECIAL = re.compile(r"([\\{}&#$%_~^])")


def _escape_latex(text: str) -> str:
    """Escape LaTeX-special characters in plain text."""
    if not text:
        return ""
    return _LATEX_SPECIAL.sub(r"\\\1", text)


def normalize_enumerate_label(enumerate_label: Optional[str]) -> str:
    """
    Normalize a high-level enumerate label hint into a safe enumitem option string.

    Examples:
        None / ""            -> "leftmargin=*"
        "Q\\arabic*."        -> "label=Q\\arabic*., leftmargin=*"
        "leftmargin=*"       -> "leftmargin=*"
        "label=Q\\arabic*."  -> "label=Q\\arabic*."

    This is intentionally conservative: when in doubt it falls back to leftmargin=*.
    """
    if not enumerate_label or not enumerate_label.strip():
        return "leftmargin=*"

    s = enumerate_label.strip()

    # If it already looks like a full option (has a key=value), trust it
    if "=" in s:
        return s

    # If it looks like a bare label expression with a counter command, wrap it
    # as a label=... with a safe left margin.
    if "\\" in s:
        return f"label={s}, leftmargin=*"

    # Otherwise, treat it as a raw option token (e.g. "leftmargin=*", "noitemsep")
    return s


def _safe_enumerate_options(enumerate_label: Optional[str]) -> str:
    """
    Backwards-compatible wrapper for older code paths.

    Prefer normalize_enumerate_label going forward.
    """
    return normalize_enumerate_label(enumerate_label)


def _set_document_latex_path(document: Document, output_tex_path: Path) -> None:
    """Ensure the in-memory Document has file_paths.latex_file pointing to the .tex file."""
    try:
        if document is None:
            return
        if document.file_paths is None:
            document.file_paths = FilePaths()
        fp = document.file_paths
        resolved = str(Path(output_tex_path).resolve())
        if isinstance(fp, dict):
            fp["latex_file"] = resolved
        else:
            try:
                fp.latex_file = resolved
            except Exception:
                # Fallback if FilePaths behaves like a mapping
                try:
                    setattr(fp, "latex_file", resolved)
                except Exception:
                    logger.debug("Could not set latex_file on document.file_paths")
    except Exception as e:
        logger.debug("Failed to set document latex path: %s", e)


def sanitize_enumerate_options(tex: str) -> str:
    """
    Fix obviously invalid enumitem options in \\begin{enumerate}[...].

    Specifically, if the option string contains a backslash (e.g. Q\\arabic*.)
    but no '=' character, we treat it as a bare label expression and rewrite it
    to label=<expr>, leftmargin=*.
    """
    pattern = re.compile(r"(\\begin\{enumerate\})\[(.*?)\]")

    def _repl(match: re.Match) -> str:
        start = match.group(1)
        opts = (match.group(2) or "").strip()
        if opts and ("\\" in opts) and ("=" not in opts):
            fixed = f"label={opts}, leftmargin=*"
            return f"{start}[{fixed}]"
        return match.group(0)

    return pattern.sub(_repl, tex)


def build_header_block(document: Document, tex_dir: Path) -> List[str]:
    """
    Build the manual header block (logo + title + subtitle + section + instructions).

    This replaces LaTeX's \\maketitle so we have full control over vertical spacing
    and avoid large gaps when a logo is present.
    """
    lines: List[str] = []

    has_logo = bool(getattr(document, "logo_path", None) and str(document.logo_path).strip())
    has_title = bool(getattr(document, "title_text", None) or getattr(document, "docid", None))
    has_subtitle = bool(getattr(document, "subtitle_text", None) and str(document.subtitle_text).strip())
    has_section = bool(getattr(document, "section_title", None) and str(document.section_title).strip())
    has_instructions = bool(
        getattr(document, "instructions_text", None) and str(document.instructions_text).strip()
    )

    # If there is no visible header content at all, return an empty block.
    if not (has_logo or has_title or has_subtitle or has_section or has_instructions):
        return lines

    # --- Centered logo + title/subtitle block ---
    lines.append("\\begin{center}")

    # Logo (only if the file exists in tex_dir and lives there)
    if has_logo:
        logo_path = Path(str(document.logo_path).strip())
        logo_resolved = logo_path.resolve() if logo_path.is_absolute() else (tex_dir / logo_path).resolve()
        logo_include: Optional[str]
        if not logo_resolved.exists():
            logger.warning("Logo path set but file not found: %s; omitting logo", logo_path)
            logo_include = None
        elif logo_resolved.parent != tex_dir:
            logger.warning("Logo file not in .tex directory; omitting logo")
            logo_include = None
        else:
            logo_include = logo_resolved.name

        if logo_include:
            width = (getattr(document, "logo_width", None) or "0.3\\textwidth").strip()
            lines.append(f"  \\includegraphics[width={width}]{{{logo_include}}}\\\\[1.5em]")

    # Title and subtitle (use docid as a fallback title)
    if has_title:
        title_text = getattr(document, "title_text", None) or getattr(document, "docid", "") or "Document"
        title_tex = _escape_latex(str(title_text).strip())
        lines.append(f"  \\textbf{{{title_tex}}}\\\\[0.5em]")

    if has_subtitle:
        subtitle_tex = _escape_latex(str(document.subtitle_text).strip())
        lines.append(f"  \\textbf{{{subtitle_tex}}}")

    lines.append("\\end{center}")
    lines.append("")

    # Fixed vertical gap before body content
    lines.append("\\vspace{2em}")
    lines.append("")

    # Optional section title and instructions, left-aligned
    if has_section:
        section_tex = _escape_latex(str(document.section_title).strip())
        # Use a bold paragraph instead of \\section{} to avoid unexpected spacing/TOC behavior
        lines.append(f"\\textbf{{{section_tex}}}")
        lines.append("")

    if has_instructions:
        instr_tex = _escape_latex(str(document.instructions_text).strip())
        lines.append(f"\\textbf{{Instructions:}} {instr_tex}")
        lines.append("")

    return lines


def build_latex_from_document(document: Document, output_tex_path: Path) -> None:
    """
    Build a .tex file from a Document and write file_paths.latex_file into the document JSON.

    Preamble: documentclass article (with optional document_class_options, geometry).
    Body: manual header (logo + title + subtitle + section + instructions), then enumerate
    with questions. Uses document layout fields (title_text, logo_path, etc.) when present.
    Escapes LaTeX-special characters in all user-provided text.

    Args:
        document: Document model (questions with stem_text, latex_stem_text, options, etc.)
        output_tex_path: Path where the .tex file will be written (e.g. run_dir/input/<doc_name>.tex)
    """
    output_tex_path = Path(output_tex_path)
    output_tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_dir = output_tex_path.parent

    # --- Preamble ---
    doc_opts = (document.document_class_options or "").strip() or "11pt"
    preamble_lines = [
        f"\\documentclass[{doc_opts}]{{article}}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage{enumitem}",
        "\\usepackage{graphicx}",
        "\\usepackage{xcolor}",
        "\\usepackage{amsmath}",
        "\\newcommand{\\rupee}{\\texttt{Rs.}}",
    ]
    if document.geometry and document.geometry.strip():
        preamble_lines.append(f"\\usepackage[{document.geometry.strip()}]{{geometry}}")
    preamble_lines.append("\\begin{document}")
    preamble = "\n".join(preamble_lines)

    # --- Body: unified manual header + enumerate with questions ---
    body_parts: List[str] = []

    # Manual header block (logo + title + subtitle + section + instructions)
    body_parts.extend(build_header_block(document, tex_dir))

    enum_opts = normalize_enumerate_label(getattr(document, "enumerate_label", None))
    body_parts.append(f"\\begin{{enumerate}}[{enum_opts}]")

    for q in document.questions:
        stem = (q.latex_stem_text or q.stem_text or "").strip()
        stem_escaped = _escape_latex(stem) if stem else ""
        body_parts.append("  \\item " + stem_escaped)
        if q.options and q.question_type.value.upper() == "MCQ":
            for key in ("A", "B", "C", "D"):
                opt = (q.options.get(key) or "").strip()
                if opt:
                    body_parts.append(f"    \\textbf{{{key}.}} " + _escape_latex(opt))
        body_parts.append("")

    body_parts.append("\\end{enumerate}")
    body_parts.append("\\end{document}")
    tex_content = preamble + "\n" + "\n".join(body_parts)
    output_tex_path.write_text(tex_content, encoding="utf-8")
    logger.info("Wrote LaTeX to %s", output_tex_path)

    # Keep in-memory document in sync with on-disk JSON
    _set_document_latex_path(document, output_tex_path)

    # Update document JSON on disk: set file_paths.latex_file
    # Document may have been loaded from run_dir/input/<doc_name>.json
    doc_json_path = output_tex_path.with_suffix(".json")
    if not doc_json_path.exists():
        logger.warning("Document JSON not found at %s; cannot set file_paths.latex_file", doc_json_path)
        return

    with doc_json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "file_paths" not in data or data["file_paths"] is None:
        data["file_paths"] = {}
    if not isinstance(data["file_paths"], dict):
        data["file_paths"] = dict(data["file_paths"]) if hasattr(data["file_paths"], "items") else {}
    # Store absolute path so orchestrator can resolve it from any cwd
    data["file_paths"]["latex_file"] = str(output_tex_path.resolve())
    with doc_json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Updated %s with file_paths.latex_file", doc_json_path)
