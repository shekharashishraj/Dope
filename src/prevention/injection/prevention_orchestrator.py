"""Prevention orchestrator: apply prevention injectors and compile PDFs.

This is intentionally separate from `src/injection/orchestrator.py` to avoid
changing detection-mode behavior.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import re

from .prevention_dual_layer_injector import apply_prevention_dual_layer
from .prevention_font_attack_injector import apply_prevention_font_attack
from .prevention_icw_injector import apply_prevention_icw
from ..constants import PREVENTION_VARIANT_GIBBERISH, PREVENTION_VARIANT_REFUSAL


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_latex_path(repo_root: Path, latex_path_str: str) -> Path:
    norm = latex_path_str.replace("\\", "/")
    p = Path(norm)
    if p.is_absolute():
        return p
    return (repo_root / p).resolve()

def _normalize_latex_for_missing_packages(tex: str) -> str:
    """Normalize LaTeX to compile on minimal TeX installs.

    Current environment is missing `enumitem.sty`, but the dataset LaTeX uses:
    - \\usepackage{enumitem}
    - \\begin{enumerate}[label=...]

    We strip enumitem and its optional arguments to keep compilation working.
    """

    # Drop enumitem package line(s)
    tex = re.sub(r"^\s*\\usepackage\{enumitem\}\s*$", "", tex, flags=re.MULTILINE)

    # Strip optional args on enumerate/itemize/description environments
    # e.g. \begin{enumerate}[label=\arabic*.] -> \begin{enumerate}
    tex = re.sub(r"(\\begin\{enumerate\})\[[^\]]*\]", r"\1", tex)
    tex = re.sub(r"(\\begin\{itemize\})\[[^\]]*\]", r"\1", tex)
    tex = re.sub(r"(\\begin\{description\})\[[^\]]*\]", r"\1", tex)

    # Remove extra blank lines introduced by stripping packages
    tex = re.sub(r"\n{3,}", "\n\n", tex)
    return tex


def _compile_latex(
    *,
    tex_source: str,
    assets_dir: Path,
    output_pdf: Path,
    require_xetex: bool = False,
    extra_font_files: Optional[List[Path]] = None,
    timeout: int = 300,
) -> Dict[str, Any]:
    temp_dir = Path(tempfile.mkdtemp(prefix="prevention_latex_compile_"))
    compile_log = output_pdf.parent / f"{output_pdf.stem}_compile.log"
    try:
        working_tex = temp_dir / "document.tex"
        working_tex.write_text(tex_source, encoding="utf-8")

        # Copy assets if any (images/pdf figures)
        if assets_dir.exists():
            for item in assets_dir.iterdir():
                if item.is_file() and item.suffix.lower() in [".png", ".jpg", ".jpeg", ".pdf"]:
                    shutil.copy2(item, temp_dir / item.name)

        # Copy fonts into fonts/ if provided (fontspec Path=fonts/)
        if extra_font_files:
            fonts_dir = temp_dir / "fonts"
            fonts_dir.mkdir(parents=True, exist_ok=True)
            for fp in extra_font_files:
                if fp.exists():
                    shutil.copy2(fp, fonts_dir / fp.name)

        compilers = ["xelatex"] if require_xetex else ["pdflatex", "xelatex"]
        success = False
        error_msg = None
        for compiler in compilers:
            try:
                proc = subprocess.run(
                    [compiler, "-interaction=nonstopmode", "document.tex"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    errors="replace",
                    timeout=timeout,
                )
                compile_log.write_text(
                    f"Compiler: {compiler}\nReturn code: {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\n",
                    encoding="utf-8",
                )
                compiled_pdf = temp_dir / "document.pdf"
                # Some TeX runs can exit non-zero due to warnings, yet still emit a PDF.
                if compiled_pdf.exists():
                    output_pdf.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(compiled_pdf, output_pdf)
                    success = True
                    break
                error_msg = f"{compiler} compilation failed (returncode={proc.returncode})"
            except FileNotFoundError:
                error_msg = f"{compiler} not found"
                continue
            except subprocess.TimeoutExpired:
                error_msg = f"{compiler} compilation timed out"
                continue

        return {"success": success, "error": error_msg, "log_path": str(compile_log)}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def generate_prevention_dual_layer_pdf(
    *,
    prevention_json_path: Path,
    output_base: Path,
    compile_pdf: bool = True,
) -> Dict[str, Any]:
    """Generate dual-layer LaTeX/PDF for a prevention JSON (single variant)."""

    repo_root = _resolve_repo_root()
    doc = json.loads(prevention_json_path.read_text(encoding="utf-8"))
    file_paths = doc.get("file_paths") or {}
    latex_file = file_paths.get("latex_file")
    if not latex_file:
        raise ValueError("Missing file_paths.latex_file in prevention JSON")

    latex_path = _resolve_latex_path(repo_root, latex_file)
    tex_content = _read_text(latex_path)

    # Flatten perturbations across all questions (stem-only per latest requirement)
    perturbations: List[Dict[str, Any]] = []
    for q in doc.get("questions", []):
        perturbations.extend(q.get("perturbations") or [])

    mutated_tex, metadata = apply_prevention_dual_layer(tex_content, perturbations)
    mutated_tex = _normalize_latex_for_missing_packages(mutated_tex)

    output_base.parent.mkdir(parents=True, exist_ok=True)
    tex_out = output_base.with_suffix(".tex")
    tex_out.write_text(mutated_tex, encoding="utf-8")

    result: Dict[str, Any] = {
        "success": True,
        "method": "dual_layer",
        "variant": (doc.get("prevention") or {}).get("variant"),
        "modified_tex_path": str(tex_out),
        "metadata": metadata,
    }

    if compile_pdf:
        pdf_out = output_base.with_suffix(".pdf")
        pdf_compile = _compile_latex(
            tex_source=mutated_tex,
            assets_dir=latex_path.parent,
            output_pdf=pdf_out,
            require_xetex=False,
        )
        result["pdf_compilation"] = pdf_compile
        if pdf_compile.get("success"):
            result["pdf_path"] = str(pdf_out)

    return result


def generate_prevention_font_attack_pdf(
    *,
    prevention_json_path: Path,
    output_base: Path,
    font_cache_dir: Path,
    compile_pdf: bool = True,
) -> Dict[str, Any]:
    """Generate font-attack LaTeX/PDF for a prevention JSON (single variant)."""

    repo_root = _resolve_repo_root()
    doc = json.loads(prevention_json_path.read_text(encoding="utf-8"))
    file_paths = doc.get("file_paths") or {}
    latex_file = file_paths.get("latex_file")
    if not latex_file:
        raise ValueError("Missing file_paths.latex_file in prevention JSON")

    latex_path = _resolve_latex_path(repo_root, latex_file)
    tex_content = _read_text(latex_path)

    perturbations: List[Dict[str, Any]] = []
    for q in doc.get("questions", []):
        perturbations.extend(q.get("perturbations") or [])

    attack = apply_prevention_font_attack(tex_content, perturbations, font_cache_dir=font_cache_dir)
    mutated_tex = _normalize_latex_for_missing_packages(attack.modified_tex)

    output_base.parent.mkdir(parents=True, exist_ok=True)
    tex_out = output_base.with_suffix(".tex")
    tex_out.write_text(mutated_tex, encoding="utf-8")

    # Resolve font files from cache
    font_files = [(font_cache_dir / name).resolve() for name in attack.font_files_needed]

    result: Dict[str, Any] = {
        "success": True,
        "method": "font_attack",
        "variant": (doc.get("prevention") or {}).get("variant"),
        "modified_tex_path": str(tex_out),
        "metadata": attack.metadata,
        "font_cache_dir": str(font_cache_dir),
        "fonts_copied": len(font_files),
    }

    if compile_pdf:
        pdf_out = output_base.with_suffix(".pdf")
        pdf_compile = _compile_latex(
            tex_source=mutated_tex,
            assets_dir=latex_path.parent,
            output_pdf=pdf_out,
            require_xetex=True,
            extra_font_files=font_files,
        )
        result["pdf_compilation"] = pdf_compile
        if pdf_compile.get("success"):
            result["pdf_path"] = str(pdf_out)

    return result


def generate_prevention_icw_dual_layer_pdf(
    *,
    prevention_json_path: Path,
    output_base: Path,
    compile_pdf: bool = True,
) -> Dict[str, Any]:
    """Hybrid: prevention ICW + prevention dual_layer."""

    repo_root = _resolve_repo_root()
    doc = json.loads(prevention_json_path.read_text(encoding="utf-8"))
    file_paths = doc.get("file_paths") or {}
    latex_file = file_paths.get("latex_file")
    if not latex_file:
        raise ValueError("Missing file_paths.latex_file in prevention JSON")

    latex_path = _resolve_latex_path(repo_root, latex_file)
    tex_content = _read_text(latex_path)

    qnums = [q.get("question_number") for q in doc.get("questions", []) if isinstance(q.get("question_number"), int)]
    tex_with_icw, icw_meta = apply_prevention_icw(tex_content, question_numbers=qnums)

    perturbations: List[Dict[str, Any]] = []
    for q in doc.get("questions", []):
        perturbations.extend(q.get("perturbations") or [])

    mutated_tex, dl_meta = apply_prevention_dual_layer(tex_with_icw, perturbations)
    mutated_tex = _normalize_latex_for_missing_packages(mutated_tex)

    output_base.parent.mkdir(parents=True, exist_ok=True)
    tex_out = output_base.with_suffix(".tex")
    tex_out.write_text(mutated_tex, encoding="utf-8")

    result: Dict[str, Any] = {
        "success": True,
        "method": "icw_dual_layer",
        "variant": (doc.get("prevention") or {}).get("variant"),
        "modified_tex_path": str(tex_out),
        "metadata": {"icw": icw_meta, "dual_layer": dl_meta},
    }

    if compile_pdf:
        pdf_out = output_base.with_suffix(".pdf")
        pdf_compile = _compile_latex(
            tex_source=mutated_tex,
            assets_dir=latex_path.parent,
            output_pdf=pdf_out,
            require_xetex=False,
        )
        result["pdf_compilation"] = pdf_compile
        if pdf_compile.get("success"):
            result["pdf_path"] = str(pdf_out)

    return result


def generate_prevention_icw_font_attack_pdf(
    *,
    prevention_json_path: Path,
    output_base: Path,
    font_cache_dir: Path,
    compile_pdf: bool = True,
) -> Dict[str, Any]:
    """Hybrid: prevention ICW + prevention font_attack."""

    repo_root = _resolve_repo_root()
    doc = json.loads(prevention_json_path.read_text(encoding="utf-8"))
    file_paths = doc.get("file_paths") or {}
    latex_file = file_paths.get("latex_file")
    if not latex_file:
        raise ValueError("Missing file_paths.latex_file in prevention JSON")

    latex_path = _resolve_latex_path(repo_root, latex_file)
    tex_content = _read_text(latex_path)

    qnums = [q.get("question_number") for q in doc.get("questions", []) if isinstance(q.get("question_number"), int)]
    tex_with_icw, icw_meta = apply_prevention_icw(tex_content, question_numbers=qnums)

    perturbations: List[Dict[str, Any]] = []
    for q in doc.get("questions", []):
        perturbations.extend(q.get("perturbations") or [])

    attack = apply_prevention_font_attack(tex_with_icw, perturbations, font_cache_dir=font_cache_dir)
    mutated_tex = _normalize_latex_for_missing_packages(attack.modified_tex)

    output_base.parent.mkdir(parents=True, exist_ok=True)
    tex_out = output_base.with_suffix(".tex")
    tex_out.write_text(mutated_tex, encoding="utf-8")

    font_files = [(font_cache_dir / name).resolve() for name in attack.font_files_needed]

    result: Dict[str, Any] = {
        "success": True,
        "method": "icw_font_attack",
        "variant": (doc.get("prevention") or {}).get("variant"),
        "modified_tex_path": str(tex_out),
        "metadata": {"icw": icw_meta, "font_attack": attack.metadata},
        "font_cache_dir": str(font_cache_dir),
        "fonts_copied": len(font_files),
    }

    if compile_pdf:
        pdf_out = output_base.with_suffix(".pdf")
        pdf_compile = _compile_latex(
            tex_source=mutated_tex,
            assets_dir=latex_path.parent,
            output_pdf=pdf_out,
            require_xetex=True,
            extra_font_files=font_files,
        )
        result["pdf_compilation"] = pdf_compile
        if pdf_compile.get("success"):
            result["pdf_path"] = str(pdf_out)

    return result


def generate_prevention_icw_pdf(
    *,
    prevention_json_path: Path,
    output_base: Path,
    compile_pdf: bool = True,
) -> Dict[str, Any]:
    """ICW-only prevention method (constant hidden prompts, no mappings needed)."""

    repo_root = _resolve_repo_root()
    doc = json.loads(prevention_json_path.read_text(encoding="utf-8"))
    file_paths = doc.get("file_paths") or {}
    latex_file = file_paths.get("latex_file")
    if not latex_file:
        raise ValueError("Missing file_paths.latex_file in prevention JSON")

    latex_path = _resolve_latex_path(repo_root, latex_file)
    tex_content = _read_text(latex_path)

    qnums = [q.get("question_number") for q in doc.get("questions", []) if isinstance(q.get("question_number"), int)]
    mutated_tex, icw_meta = apply_prevention_icw(tex_content, question_numbers=qnums)
    mutated_tex = _normalize_latex_for_missing_packages(mutated_tex)

    output_base.parent.mkdir(parents=True, exist_ok=True)
    tex_out = output_base.with_suffix(".tex")
    tex_out.write_text(mutated_tex, encoding="utf-8")

    result: Dict[str, Any] = {
        "success": True,
        "method": "icw",
        "variant": None,
        "modified_tex_path": str(tex_out),
        "metadata": icw_meta,
    }

    if compile_pdf:
        pdf_out = output_base.with_suffix(".pdf")
        pdf_compile = _compile_latex(
            tex_source=mutated_tex,
            assets_dir=latex_path.parent,
            output_pdf=pdf_out,
            require_xetex=False,
        )
        result["pdf_compilation"] = pdf_compile
        if pdf_compile.get("success"):
            result["pdf_path"] = str(pdf_out)

    return result

