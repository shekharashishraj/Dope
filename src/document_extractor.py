"""LLM-based document extraction from PDF and optional answer key."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pydantic import ValidationError

from .models.perturbation import Document, Question
from .models.enums import QuestionType
from .stem_utils import normalize_latex_stem

logger = logging.getLogger(__name__)

try:
    import fitz
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False


def _extract_layout_and_renders(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 200,
) -> Optional[Dict[str, Any]]:
    """
    Extract lightweight layout metadata per page and render PNGs for vision input.
    Returns dict with layout_path, page_images (relative paths), and in-memory layout JSON.
    """
    if not FITZ_AVAILABLE:
        return None
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    page_images_dir = output_dir / "page_images"
    page_images_dir.mkdir(parents=True, exist_ok=True)
    layout: List[Dict[str, Any]] = []
    page_image_paths: List[str] = []
    try:
        doc = fitz.open(str(pdf_path))
        try:
            for page_index, page in enumerate(doc):
                page_info: Dict[str, Any] = {
                    "page_index": page_index,
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "blocks": [],
                    "images": [],
                }
                # Text blocks with basic font/size hints
                try:
                    text_dict = page.get_text("dict")
                    for block in text_dict.get("blocks", []):
                        if block.get("type") != 0:
                            continue
                        blk: Dict[str, Any] = {"bbox": block.get("bbox"), "lines": []}
                        for line in block.get("lines", []):
                            line_entry = {"bbox": line.get("bbox"), "spans": []}
                            for span in line.get("spans", []):
                                line_entry["spans"].append(
                                    {
                                        "text": span.get("text"),
                                        "size": span.get("size"),
                                        "font": span.get("font"),
                                        "bbox": span.get("bbox"),
                                    }
                                )
                            blk["lines"].append(line_entry)
                        page_info["blocks"].append(blk)
                except Exception as e:
                    logger.debug("Failed to extract text blocks on page %s: %s", page_index, e)
                # Image metadata
                try:
                    for img in page.get_images(full=True):
                        xref = img[0]
                        bbox = None
                        try:
                            bbox = page.get_image_bbox(xref)
                        except Exception:
                            bbox = None
                        page_info["images"].append(
                            {
                                "xref": xref,
                                "bbox": bbox,
                                "width": img[2],
                                "height": img[3],
                                "cs": img[4],
                                "bpc": img[5],
                            }
                        )
                except Exception as e:
                    logger.debug("Failed to extract image metadata on page %s: %s", page_index, e)
                # Render page to PNG
                try:
                    pix = page.get_pixmap(dpi=dpi, alpha=False)
                    filename = f"page_{page_index + 1}.png"
                    out_path = page_images_dir / filename
                    pix.save(str(out_path))
                    page_image_paths.append(str(Path("page_images") / filename))
                    page_info["render"] = {"image": str(Path("page_images") / filename), "dpi": dpi}
                except Exception as e:
                    logger.warning("Failed to render page %s: %s", page_index, e)
                layout.append(page_info)
        finally:
            doc.close()
    except Exception as e:
        logger.warning("Layout extraction failed: %s", e)
        return None

    layout_json = {"pages": layout}
    layout_path = output_dir / "layout.json"
    try:
        layout_path.write_text(json.dumps(layout_json, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to write layout.json: %s", e)
    return {
        "layout_path": layout_path,
        "page_images": page_image_paths,
        "layout": layout_json,
    }


EXTRACT_SYSTEM_PROMPT = """You are an expert at extracting structured question data from quiz/exam PDFs.
Given the raw text extracted from a PDF (and optionally an answer key), produce a single JSON object that matches this schema exactly:
- docid: string (document identifier, use the one provided or infer from content)
- domain: string (e.g. "upload" if unknown)
- academic_level: string (e.g. "unknown" if not specified)
- questions: array of question objects, each with:
  - question_number: integer (1-based)
  - question_type: one of "MCQ", "TF", "LONG"
  - stem_text: string (the question text as it appears, plain text)
  - latex_stem_text: string (question text only, no "Q1."/label prefix; same as stem_text or LaTeX-escaped; use double backticks for quotes)
  - options: object for MCQ with keys "A", "B", "C", "D" and string values; omit for TF/LONG
  - gold_answer: string (correct answer: option letter for MCQ, "True"/"False" for TF, or summary for LONG)
Optional layout fields (include only if you can infer them from the PDF text):
- title_text: string (main title line at top, e.g. course code and name)
- subtitle_text: string (subtitle line, e.g. "Quiz 1")
- section_title: string (section heading before questions, e.g. "Multiple Choice Questions (Single correct)")
- instructions_text: string (instructions line, e.g. "Instructions: Select the correct option with a short explanation.")
- geometry: string (e.g. "margin=1in" if document suggests standard margins)
- document_class_options: string (e.g. "12pt")
- enumerate_label: string (e.g. "Q\\\\arabic*." for "Q1.", "Q2." style numbering)
Return ONLY valid JSON with no markdown or explanation. The root object must have keys: docid, domain, academic_level, questions."""


def extract_images_from_pdf(
    pdf_path: Path,
    output_dir: Path,
    max_images: int = 10,
) -> List[Dict[str, Any]]:
    """
    Extract images from the first page of a PDF and save them to output_dir.
    Returns a list of {"path": filename, "width": "2.5cm" or None}.
    """
    if not FITZ_AVAILABLE:
        return []
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result: List[Dict[str, Any]] = []
    try:
        doc = fitz.open(str(pdf_path))
        try:
            if len(doc) == 0:
                return result
            page = doc[0]
            image_list = page.get_images(full=True)
            for i, item in enumerate(image_list[:max_images]):
                xref = item[0]
                try:
                    base_image = doc.extract_image(xref)
                    img_bytes = base_image.get("image")
                    ext = base_image.get("ext", "png").lower()
                    if ext not in ("png", "jpg", "jpeg"):
                        ext = "png"
                    if len(image_list) == 1:
                        filename = "logo.png"
                    else:
                        filename = f"header_image_{i}.png"
                    out_path = output_dir / filename
                    with open(out_path, "wb") as f:
                        f.write(img_bytes)
                    width = "2.5cm" if i == 0 else None
                    result.append({"path": filename, "width": width})
                except Exception as e:
                    logger.debug("Skip image xref %s: %s", xref, e)
                    continue
        finally:
            doc.close()
    except Exception as e:
        logger.warning("Image extraction failed: %s", e)
    return result


def _extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF."""
    if not FITZ_AVAILABLE:
        raise RuntimeError("PyMuPDF (fitz) is required for PDF text extraction. Install with: pip install PyMuPDF")
    doc = fitz.open(str(pdf_path))
    try:
        parts = []
        for page in doc:
            parts.append(page.get_text())
        return "\n\n".join(parts).strip()
    finally:
        doc.close()


def _read_answer_key(answer_key_path: Optional[Path]) -> dict:
    """Read answer key file and return mapping question_number -> gold_answer."""
    if not answer_key_path or not answer_key_path.exists():
        return {}
    text = answer_key_path.read_text(encoding="utf-8", errors="replace").strip()
    mapping = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Try "1. A" or "Q1 A" or "1: A" or "Question 1: A"
        for sep in (".", ":", "\t"):
            if sep in line:
                left, _, right = line.partition(sep)
                left = left.strip().lstrip("Qq uestion").strip()
                right = right.strip()
                try:
                    num = int(left)
                    mapping[num] = right
                    break
                except ValueError:
                    continue
    return mapping


def _parse_document_from_llm_response(content: str, doc_id: str) -> Document:
    """Parse LLM response into Document model."""
    # Remove markdown code fence if present
    raw = content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    data = json.loads(raw)
    if "docid" not in data:
        data["docid"] = doc_id
    if "domain" not in data or not data["domain"]:
        data["domain"] = "upload"
    if "academic_level" not in data or not data["academic_level"]:
        data["academic_level"] = "unknown"
    # Normalize question_type to enum values
    for q in data.get("questions", []):
        qt = q.get("question_type", "MCQ")
        if isinstance(qt, str):
            qt = qt.upper().strip()
            if qt not in ("MCQ", "TF", "LONG"):
                qt = "MCQ"
            q["question_type"] = qt
        if not q.get("latex_stem_text") and q.get("stem_text"):
            q["latex_stem_text"] = q["stem_text"]
        q["latex_stem_text"] = normalize_latex_stem(q.get("latex_stem_text") or q.get("stem_text") or "")
    # Preserve optional layout keys if present (strip empty strings to None)
    for key in ("title_text", "subtitle_text", "section_title", "instructions_text", "geometry", "document_class_options", "enumerate_label"):
        if key in data and (data[key] is None or (isinstance(data[key], str) and not data[key].strip())):
            data[key] = None
    return Document.model_validate(data)


def extract_document_from_pdf(
    pdf_path: Path,
    answer_key_path: Optional[Path],
    doc_id: str,
    output_json_path: Path,
    pdf_path_for_file_paths: Path,
    config: Any,
    output_dir: Optional[Path] = None,
    extract_images: bool = True,
    max_images_first_page: int = 5,
    page_render_dpi: int = 200,
) -> Document:
    """
    Extract document (questions, options, gold answers) from PDF using LLM.
    Writes Document to output_json_path with file_paths.pdf_file set.
    file_paths.latex_file is left unset; latex_reconstructor sets it later.
    When output_dir is set, extracts images from the first page and sets logo_path/logo_width on Document.

    Args:
        pdf_path: Path to uploaded PDF.
        answer_key_path: Optional path to answer key file (text/CSV).
        doc_id: Document identifier (e.g. stem of PDF filename).
        output_json_path: Where to write the extracted document JSON.
        pdf_path_for_file_paths: Path to store in file_paths.pdf_file (e.g. run_dir/uploads/name.pdf).
        config: Config object (for OpenAI API key and model).
        output_dir: If set, images are extracted here and logo_path/logo_width set on Document.
        extract_images: Whether to extract images from the first page when output_dir is set.
        max_images_first_page: Max number of images to extract from the first page.

    Returns:
        Document model instance.
    """
    pdf_text = _extract_text_from_pdf(pdf_path)
    answer_mapping = _read_answer_key(answer_key_path)

    answer_key_section = ""
    if answer_mapping:
        answer_key_section = f"\n\nAnswer key (question_number -> gold_answer):\n{json.dumps(answer_mapping, indent=2)}"

    user_prompt = f"""Document id: {doc_id}

Extract all questions from the following PDF text. For each question, set question_number, question_type (MCQ, TF, or LONG), stem_text, latex_stem_text (same as stem_text or LaTeX-escaped), options (for MCQ only, keys A,B,C,D), and gold_answer.
If the PDF text contains a main title at the top (e.g. course code and name), a subtitle (e.g. "Quiz 1"), a section heading (e.g. "Multiple Choice Questions"), or an instructions line, include them as title_text, subtitle_text, section_title, and instructions_text. If question numbering looks like "Q1.", "Q2.", set enumerate_label to "Q\\\\arabic*." (with two backslashes).
{answer_key_section}

PDF text:
---
{pdf_text[:12000]}
---
Return a single JSON object with keys docid, domain, academic_level, questions. Use domain="upload" and academic_level="unknown" if not specified. Optionally include title_text, subtitle_text, section_title, instructions_text, geometry, document_class_options, enumerate_label when inferable from the text."""

    api_key = getattr(config.openai, "api_key", None) or __import__("os").environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY or config.openai.api_key.")
    client = OpenAI(api_key=api_key)
    model = getattr(config.openai, "model", "gpt-4o")
    timeout = getattr(config.openai, "timeout", 120)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        timeout=timeout,
    )
    content = response.choices[0].message.content or "{}"
    doc = _parse_document_from_llm_response(content, doc_id)

    # Extract images from first page when output_dir is provided
    if output_dir and extract_images:
        images = extract_images_from_pdf(pdf_path, output_dir, max_images=max_images_first_page)
        if images:
            doc.logo_path = images[0]["path"]
            doc.logo_width = images[0].get("width") or "2.5cm"

    # Extract layout metadata and page renders for vision reconstructor
    layout_info = None
    if output_dir:
        layout_info = _extract_layout_and_renders(pdf_path, output_dir, dpi=page_render_dpi)

    # Apply answer key overrides if we have them
    if answer_mapping:
        for q in doc.questions:
            if q.question_number in answer_mapping:
                q.gold_answer = answer_mapping[q.question_number]

    # Set file_paths.pdf_file for downstream; latex_file set by latex_reconstructor
    if doc.file_paths is None:
        from .models.perturbation import FilePaths
        doc.file_paths = FilePaths()
    if not hasattr(doc.file_paths, "model_dump"):
        fp = doc.file_paths
        if isinstance(fp, dict):
            fp["pdf_file"] = str(pdf_path_for_file_paths)
            if layout_info and layout_info.get("layout_path"):
                fp["layout_json"] = str(layout_info["layout_path"])
            if layout_info and layout_info.get("page_images"):
                fp["page_images"] = layout_info["page_images"]
        else:
            setattr(doc.file_paths, "pdf_file", str(pdf_path_for_file_paths))
            if layout_info and layout_info.get("layout_path"):
                setattr(doc.file_paths, "layout_json", str(layout_info["layout_path"]))
            if layout_info and layout_info.get("page_images"):
                setattr(doc.file_paths, "page_images", layout_info["page_images"])
    else:
        d = doc.file_paths.model_dump() if hasattr(doc.file_paths, "model_dump") else dict(doc.file_paths)
        d["pdf_file"] = str(pdf_path_for_file_paths)
        if layout_info and layout_info.get("layout_path"):
            d["layout_json"] = str(layout_info["layout_path"])
        if layout_info and layout_info.get("page_images"):
            d["page_images"] = layout_info["page_images"]
        from .models.perturbation import FilePaths
        doc.file_paths = FilePaths(**d) if hasattr(FilePaths, "model_validate") else type(doc.file_paths)(**d)

    # Ensure file_paths is serializable (FilePaths has extra="allow" so pdf_file is allowed)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    data = doc.model_dump()
    if "file_paths" not in data or data["file_paths"] is None:
        data["file_paths"] = {}
    if isinstance(data["file_paths"], dict):
        data["file_paths"]["pdf_file"] = str(pdf_path_for_file_paths)
        if layout_info and layout_info.get("layout_path"):
            data["file_paths"]["layout_json"] = str(layout_info["layout_path"])
        if layout_info and layout_info.get("page_images"):
            data["file_paths"]["page_images"] = layout_info["page_images"]
    with output_json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Wrote extracted document to %s", output_json_path)
    return doc
