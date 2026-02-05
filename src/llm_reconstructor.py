"\"\"\"Vision-assisted LaTeX reconstruction using page renders + layout metadata.\"\"\""
import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .latex_reconstructor import (
    _escape_latex,
    _set_document_latex_path,
    normalize_enumerate_label,
    sanitize_enumerate_options,
)
from .models.perturbation import Document

logger = logging.getLogger(__name__)


def _encode_image_to_data_url(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _build_preamble(document: Document) -> str:
    doc_opts = (document.document_class_options or "").strip() or "11pt"
    lines = [
        f"\\documentclass[{doc_opts}]{{article}}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage{enumitem}",
        "\\usepackage{graphicx}",
        "\\usepackage{xcolor}",
    ]
    if document.geometry and document.geometry.strip():
        lines.append(f"\\usepackage[{document.geometry.strip()}]{{geometry}}")
    title_tex = _escape_latex(document.title_text or document.docid or "Document")
    lines.append(f"\\title{{{title_tex}}}")
    if not (document.title_text or document.logo_path or document.section_title):
        lines.append("\\author{IGSHIELD Reconstructed}")
    lines.append("\\date{}")
    lines.append("\\begin{document}")
    return "\n".join(lines)


def _semantic_summary(document: Document) -> str:
    parts = []
    if document.title_text:
        parts.append(f"Title: {document.title_text}")
    if document.subtitle_text:
        parts.append(f"Subtitle: {document.subtitle_text}")
    if document.section_title:
        parts.append(f"Section: {document.section_title}")
    if document.instructions_text:
        parts.append(f"Instructions: {document.instructions_text}")
    for q in document.questions:
        opt_text = ""
        if q.options:
            opt_parts = [f"{k}) {v}" for k, v in q.options.items() if v]
            opt_text = " Options: " + "; ".join(opt_parts)
        parts.append(f"Q{q.question_number}: {q.stem_text}{opt_text}")
    return "\n".join(parts)


def _page_prompt_text(document: Document, page_meta: Dict[str, Any], semantic: str) -> str:
    layout_snippet = json.dumps(page_meta, ensure_ascii=False)
    return (
        "You are reconstructing LaTeX for a PDF page. "
        "Return ONLY LaTeX body content for this page (no preamble, no \\begin{document}/\\end{document}). "
        "Preserve visual layout: headings, spacing, lists, numbering, bold/italics, and image placement/sizing. "
        "Use includegraphics with the provided image filenames; do NOT invent assets. "
        "Honor enumerate labels if present. Keep math as-is. "
        f"\n\nSemantic content summary:\n{semantic}"
        f"\n\nPage layout metadata (JSON):\n{layout_snippet}\n"
    )


def _call_vision(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_text: str,
    image_path: Path,
    temperature: Optional[float],
    max_completion_tokens: Optional[int],
) -> str:
    content: List[Dict[str, Any]] = [
        {"type": "text", "text": user_text},
        {
            "type": "image_url",
            "image_url": {"url": _encode_image_to_data_url(image_path)},
        },
    ]
    kwargs = {}
    if max_completion_tokens is not None:
        kwargs["max_completion_tokens"] = max_completion_tokens
    if temperature is not None:
        kwargs["temperature"] = temperature

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        **kwargs,
    )
    return resp.choices[0].message.content or ""


def build_latex_with_vision(
    document: Document,
    layout_json_path: Optional[Path],
    page_image_paths: Optional[List[str]],
    config: Any,
    output_tex_path: Path,
) -> str:
    """
    Build LaTeX using a vision-capable model. Writes to output_tex_path and returns the string.
    """
    model = getattr(config.processing, "vision_model", "gpt-5.1-2025-11-13")
    mode = getattr(config.processing, "vision_mode", "per_page")
    temperature = getattr(config.processing, "vision_temperature", None)
    max_completion_tokens = getattr(
        config.processing,
        "vision_max_completion_tokens",
        None,
    )
    # Backward compatibility: if the new field is not set, fall back to vision_max_tokens
    if max_completion_tokens is None:
        max_completion_tokens = getattr(config.processing, "vision_max_tokens", None)

    api_key = getattr(config.openai, "api_key", None) or __import__("os").environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found for vision reconstruction.")
    client = OpenAI(api_key=api_key)

    preamble = _build_preamble(document)
    semantic = _semantic_summary(document)
    layout_data = None
    if layout_json_path and Path(layout_json_path).exists():
        try:
            layout_data = json.loads(Path(layout_json_path).read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to read layout JSON: %s", e)

    if not page_image_paths:
        raise ValueError("No page renders available for vision reconstruction.")

    page_fragments: List[str] = []
    system_prompt = (
        "You are an expert LaTeX compositor. Given a page render (image), layout metadata, and semantic content, "
        "produce LaTeX body that visually matches the page. Do not include a preamble or document environment."
    )

    if mode == "full_doc":
        # Send all pages as images; still expect a single body.
        content_parts: List[Dict[str, Any]] = [
            {"type": "text", "text": _page_prompt_text(document, layout_data or {}, semantic)}
        ]
        for img_rel in page_image_paths:
            img_path = Path(layout_json_path).parent / img_rel if layout_json_path else Path(img_rel)
            content_parts.append({"type": "image_url", "image_url": {"url": _encode_image_to_data_url(img_path)}})
        kwargs = {}
        if max_completion_tokens is not None:
            kwargs["max_completion_tokens"] = max_completion_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_parts},
            ],
            **kwargs,
        )
        body = resp.choices[0].message.content or ""
        page_fragments.append(body.strip())
    else:
        pages_meta = (layout_data or {}).get("pages", []) if layout_data else []
        for idx, img_rel in enumerate(page_image_paths):
            img_path = Path(layout_json_path).parent / img_rel if layout_json_path else Path(img_rel)
            page_meta = pages_meta[idx] if idx < len(pages_meta) else {}
            user_text = _page_prompt_text(document, page_meta, semantic)
            logger.info("Vision reconstruction page %s using %s", idx + 1, model)
            fragment = _call_vision(
                client=client,
                model=model,
                system_prompt=system_prompt,
                user_text=user_text,
                image_path=img_path,
                temperature=temperature,
                max_completion_tokens=max_completion_tokens,
            )
            page_fragments.append(fragment.strip())

    body = "\n\n\\clearpage\n\n".join(page_fragments)
    tex_content = preamble + "\n" + body + "\n\\end{document}"
    output_tex_path = Path(output_tex_path)
    output_tex_path.parent.mkdir(parents=True, exist_ok=True)
    output_tex_path.write_text(tex_content, encoding="utf-8")
    logger.info("Vision-based LaTeX written to %s", output_tex_path)

    # Ensure in-memory document has latex_file set
    if not hasattr(document, "file_paths") or document.file_paths is None:
        from .models.perturbation import FilePaths
        document.file_paths = FilePaths()
    if isinstance(document.file_paths, dict):
        document.file_paths["latex_file"] = str(output_tex_path.resolve())
    else:
        try:
            document.file_paths.latex_file = str(output_tex_path.resolve())
        except Exception:
            try:
                setattr(document.file_paths, "latex_file", str(output_tex_path.resolve()))
            except Exception:
                pass

    # Mirror heuristic reconstructor: update JSON on disk with latex_file (and layout/page images if available)
    json_path = output_tex_path.with_suffix(".json")
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            if "file_paths" not in data or data["file_paths"] is None:
                data["file_paths"] = {}
            elif not isinstance(data["file_paths"], dict):
                data["file_paths"] = dict(data["file_paths"]) if hasattr(data["file_paths"], "items") else {}
            data["file_paths"]["latex_file"] = str(output_tex_path.resolve())
            if layout_json_path:
                data["file_paths"].setdefault("layout_json", str(Path(layout_json_path).resolve()))
            if page_image_paths:
                data["file_paths"].setdefault("page_images", page_image_paths)
            json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.info("Updated %s with file_paths.latex_file via vision path", json_path)
        except Exception as e:
            logger.warning("Failed to update %s with latex_file after vision reconstruction: %s", json_path, e)

    return tex_content


def refine_layout_with_vision(
    document: Document,
    layout_json_path: Optional[Path],
    page_image_paths: Optional[List[str]],
    config: Any,
) -> Document:
    """
    Use a vision-capable model to refine high-level layout fields on the Document
    (titles, subtitles, section headings, instructions, logo hints), without
    generating raw LaTeX. Returns the updated Document.
    """
    if not layout_json_path or not page_image_paths:
        return document

    model = getattr(config.processing, "vision_model", "gpt-5.1-2025-11-13")
    temperature = getattr(config.processing, "vision_temperature", None)
    max_completion_tokens = getattr(
        config.processing,
        "vision_max_completion_tokens",
        None,
    )
    if max_completion_tokens is None:
        max_completion_tokens = getattr(config.processing, "vision_max_tokens", None)

    api_key = getattr(config.openai, "api_key", None) or __import__("os").environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found for vision layout refinement.")
    client = OpenAI(api_key=api_key)

    layout_data = None
    if layout_json_path and Path(layout_json_path).exists():
        try:
            layout_data = json.loads(Path(layout_json_path).read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to read layout JSON for layout refinement: %s", e)

    # Use first page image for layout inference (sufficient for quiz-style docs)
    first_img_rel = page_image_paths[0]
    img_path = Path(layout_json_path).parent / first_img_rel if layout_json_path else Path(first_img_rel)

    semantic = _semantic_summary(document)
    first_page_meta = {}
    if layout_data and isinstance(layout_data, dict):
        pages = layout_data.get("pages") or []
        if pages:
            first_page_meta = pages[0]

    system_prompt = (
        "You are an expert at understanding the visual layout of exam/quiz PDFs.\n"
        "Given a rendered page image, some extracted text/questions, and layout metadata, "
        "you must return ONLY a JSON object with refined high-level layout fields. "
        "You MUST NOT include any LaTeX markup (no \\begin, no \\end, no commands)."
    )

    user_text = (
        "Use the page image and info below to refine these fields if needed:\n"
        "- title_text (main title at top, e.g., course code & name)\n"
        "- subtitle_text (e.g., 'Quiz 1')\n"
        "- section_title (e.g., 'Multiple Choice Questions (Single correct)')\n"
        "- instructions_text (instructions line near the questions)\n"
        "- enumerate_label (e.g., 'Q\\\\arabic*.' if questions are labeled Q1., Q2., ...)\n"
        "- logo_position (one of 'top_left', 'top_center', 'top_right' if clearly visible)\n"
        "- logo_width (a LaTeX width like '2.5cm' if you can infer a reasonable size)\n\n"
        "Existing semantic extraction summary:\n"
        f"{semantic}\n\n"
        "First page layout metadata (JSON snippet):\n"
        f"{json.dumps(first_page_meta, ensure_ascii=False)}\n\n"
        "Return ONLY a single JSON object with any of these keys you can refine. "
        "Do not include comments, markdown, or surrounding text."
    )

    content: List[Dict[str, Any]] = [
        {"type": "text", "text": user_text},
        {"type": "image_url", "image_url": {"url": _encode_image_to_data_url(img_path)}},
    ]

    kwargs = {}
    if max_completion_tokens is not None:
        kwargs["max_completion_tokens"] = max_completion_tokens
    if temperature is not None:
        kwargs["temperature"] = temperature

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        **kwargs,
    )
    raw = resp.choices[0].message.content or "{}"

    # Strip code fences if any
    raw_stripped = raw.strip()
    if raw_stripped.startswith("```"):
        lines = raw_stripped.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_stripped = "\n".join(lines)

    try:
        layout_updates = json.loads(raw_stripped)
    except Exception as e:
        logger.warning("Vision layout refinement returned non-JSON content: %s", e)
        return document

    if not isinstance(layout_updates, dict):
        return document

    # Apply refined fields if present
    def _apply(key: str):
        value = layout_updates.get(key)
        if isinstance(value, str) and value.strip():
            setattr(document, key, value.strip())

    for key in (
        "title_text",
        "subtitle_text",
        "section_title",
        "instructions_text",
        "enumerate_label",
        "logo_width",
        "logo_position",
    ):
        _apply(key)

    return document


def _strip_code_fences(text: str) -> str:
    """Remove surrounding markdown code fences if present."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped


def _validate_template_latex(tex: str) -> bool:
    """
    Basic sanity checks for template-generated LaTeX.

    - Exactly one \\documentclass
    - Exactly one \\begin{document} / \\end{document}
    - Matching single enumerate environment
    """
    try:
        if tex.count("\\documentclass") != 1:
            return False
        if tex.count("\\begin{document}") != 1 or tex.count("\\end{document}") != 1:
            return False
        begin_enum = tex.count("\\begin{enumerate}")
        end_enum = tex.count("\\end{enumerate}")
        if begin_enum != end_enum:
            return False
        if begin_enum == 0:
            return False
    except Exception:
        return False
    return True


def build_latex_with_vision_template(
    document: Document,
    layout_json_path: Optional[Path],
    page_image_paths: Optional[List[str]],
    config: Any,
    output_tex_path: Path,
) -> str:
    """
    Template-constrained full LaTeX reconstruction using a vision-capable model.

    The model receives:
      - A fixed LaTeX skeleton with markers
      - A description of the allowed micro-language for each marker
      - Document semantic summary and JSON
      - First page layout metadata + rendered image

    It must return a single complete .tex document following the skeleton.
    """
    if not layout_json_path or not page_image_paths:
        raise ValueError("Layout JSON and page renders are required for vision template reconstruction.")

    model = getattr(config.processing, "vision_model", "gpt-5.1-2025-11-13")
    temperature = getattr(config.processing, "vision_temperature", None)
    max_completion_tokens = getattr(
        config.processing,
        "vision_max_completion_tokens",
        None,
    )
    if max_completion_tokens is None:
        max_completion_tokens = getattr(config.processing, "vision_max_tokens", None)

    api_key = getattr(config.openai, "api_key", None) or __import__("os").environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found for vision template reconstruction.")
    client = OpenAI(api_key=api_key)

    # Load layout metadata (first page is usually enough for quiz layout)
    layout_data: Optional[Dict[str, Any]] = None
    if layout_json_path and Path(layout_json_path).exists():
        try:
            layout_data = json.loads(Path(layout_json_path).read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to read layout JSON for vision template reconstruction: %s", e)

    pages_meta = (layout_data or {}).get("pages") or []
    first_page_meta = pages_meta[0] if pages_meta else {}

    first_img_rel = page_image_paths[0]
    img_path = Path(layout_json_path).parent / first_img_rel if layout_json_path else Path(first_img_rel)

    semantic = _semantic_summary(document)
    # Compact JSON snapshot of the document (questions, options, titles)
    try:
        doc_json = document.model_dump(mode="json")
    except Exception:
        doc_json = {}

    enum_opts = normalize_enumerate_label(getattr(document, "enumerate_label", None))

    skeleton = (
        "\\documentclass[11pt]{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage{enumitem}\n"
        "\\usepackage{graphicx}\n"
        "\\usepackage{xcolor}\n\n"
        "\\begin{document}\n\n"
        "<<<LOGO_BLOCK>>>\n\n"
        "\\begin{center}\n"
        "<<<TITLE>>>\n"
        "\\\\% optional subtitle line(s)\n"
        "<<<SUBTITLE_BLOCK>>>\n"
        "\\end{center}\n\n"
        "\\vspace{2em}\n\n"
        "<<<SECTION_TITLE_BLOCK>>>\n"
        "<<<INSTRUCTIONS_BLOCK>>>\n\n"
        f"\\begin{{enumerate}}[{enum_opts}]\n"
        "<<<QUESTIONS_BLOCK>>>\n"
        "\\end{enumerate}\n\n"
        "\\end{document}\n"
    )

    system_prompt = (
        "You are an expert LaTeX compositor for exams/quizzes.\n"
        "You are given a fixed LaTeX skeleton with markers and must return a SINGLE complete .tex document.\n"
        "You MUST preserve the skeleton structure and only replace the markers with allowed content.\n\n"
        "Skeleton (do not change structure, only replace markers):\n"
        f"{skeleton}\n\n"
        "Allowed micro-language for each marker:\n"
        "- <<<LOGO_BLOCK>>>: either empty, or a logo block placed near the top such as:\n"
        "    \\begin{center}\\includegraphics[width=0.25\\textwidth]{logo.png}\\\\[1.5em]\\end{center}\n"
        "  or just an \\includegraphics line followed by \\\\[1.5em]. Do NOT use \\maketitle.\n"
        "- <<<TITLE>>>: plain text title to appear inside the existing center block; you may use \\textbf{} "
        "and \\\\ for line breaks, but do not start new environments.\n"
        "- <<<SUBTITLE_BLOCK>>>: optional subtitle text (e.g. \\textbf{...}) that also lives inside the "
        "same center block under the title; keep it simple text with optional \\\\ for line breaks.\n"
        "- <<<SECTION_TITLE_BLOCK>>> and <<<INSTRUCTIONS_BLOCK>>>: simple left-aligned text using "
        "\\textbf{}, \\emph{}, plain paragraphs, and \\\\ for line breaks. No new sections/environments.\n"
        "- <<<QUESTIONS_BLOCK>>>: ONLY a sequence of question items:\n"
        "    \\item <question text>\n"
        "    \\textbf{A.} <option text>\n"
        "    \\textbf{B.} <option text>\n"
        "    ...\n"
        "  No \\begin{enumerate} or \\end{enumerate} here (they are already in the skeleton).\n"
        "  Do NOT add \\begin{document}, \\section, \\maketitle, or other environments.\n\n"
        "You MUST NOT add another \\documentclass, \\begin{document}, or additional enumerate environments.\n"
        "Return ONLY the final LaTeX document text. Do NOT wrap it in markdown code fences."
    )

    user_text = (
        "Use the page image, layout metadata, and extracted content below to fill in the skeleton markers.\n\n"
        "High-level semantic summary:\n"
        f"{semantic}\n\n"
        "Document JSON snapshot (titles, questions, options):\n"
        f"{json.dumps(doc_json, ensure_ascii=False)[:8000]}\n\n"
        "First page layout metadata (JSON snippet):\n"
        f"{json.dumps(first_page_meta, ensure_ascii=False)}\n\n"
        "Return a single LaTeX document based on the skeleton with all markers replaced. "
        "Do not include explanations or markdown, only LaTeX."
    )

    content: List[Dict[str, Any]] = [
        {"type": "text", "text": user_text},
        {"type": "image_url", "image_url": {"url": _encode_image_to_data_url(img_path)}},
    ]

    kwargs: Dict[str, Any] = {}
    if max_completion_tokens is not None:
        kwargs["max_completion_tokens"] = max_completion_tokens
    if temperature is not None:
        kwargs["temperature"] = temperature

    logger.info("Calling vision template reconstruction with model %s", model)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        **kwargs,
    )
    raw = resp.choices[0].message.content or ""
    tex_content = _strip_code_fences(raw)
    tex_content = sanitize_enumerate_options(tex_content)

    if not _validate_template_latex(tex_content):
        logger.warning("Vision template LaTeX failed validation; falling back to heuristic builder")
        from .latex_reconstructor import build_latex_from_document

        build_latex_from_document(document, output_tex_path)
        return tex_content

    output_tex_path = Path(output_tex_path)
    output_tex_path.parent.mkdir(parents=True, exist_ok=True)
    output_tex_path.write_text(tex_content, encoding="utf-8")
    logger.info("Vision template-based LaTeX written to %s", output_tex_path)

    # Keep in-memory document in sync with on-disk JSON
    _set_document_latex_path(document, output_tex_path)

    # Update JSON on disk with latex_file (and reuse existing file_paths if present)
    json_path = output_tex_path.with_suffix(".json")
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            if "file_paths" not in data or data["file_paths"] is None:
                data["file_paths"] = {}
            elif not isinstance(data["file_paths"], dict):
                data["file_paths"] = dict(data["file_paths"]) if hasattr(data["file_paths"], "items") else {}
            data["file_paths"]["latex_file"] = str(output_tex_path.resolve())
            if layout_json_path:
                data["file_paths"].setdefault("layout_json", str(Path(layout_json_path).resolve()))
            if page_image_paths:
                data["file_paths"].setdefault("page_images", page_image_paths)
            json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info("Updated %s with file_paths.latex_file via vision template path", json_path)
        except Exception as e:
            logger.warning(
                "Failed to update %s with latex_file after vision template reconstruction: %s",
                json_path,
                e,
            )

    return tex_content

