import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config import Config
from src.processor import Processor
from src.pdf_generator import OrganizedPDFGenerator
from src.detection.test import find_perturbed_pdfs
from src.detection.response_collector import ResponseCollector
from src.detection.signature_matcher import SignatureMatcher
from src.detection.metrics_calculator import MetricsCalculator
from src.models.perturbation import Document
from src.document_extractor import extract_document_from_pdf
from src.latex_reconstructor import build_latex_from_document
from src.llm_reconstructor import refine_layout_with_vision, build_latex_with_vision_template

ROOT = Path(__file__).resolve().parent.parent
RUNS_ROOT = ROOT / "backend" / "runs"
LOGS_ROOT = ROOT / "backend" / "logs"

RUNS_ROOT.mkdir(parents=True, exist_ok=True)
LOGS_ROOT.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("igshield.api")
logger.setLevel(logging.INFO)

if not logger.handlers:
    log_path = LOGS_ROOT / "api.log"
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


class RunContext(BaseModel):
    run_id: str
    created_at: str
    doc_name: str
    upload_dir: str
    run_timestamp: Optional[str] = None  # YYYYMMDD_HHMMSS for output_attacked_pdfs/<run_timestamp>/
    pdf_path: Optional[str] = None
    answer_key_path: Optional[str] = None
    document_json_path: Optional[str] = None  # run_dir/input/<doc_name>.json after extract
    perturbation_jsons: List[str] = Field(default_factory=list)
    attacked_output_dir: Optional[str] = None
    attacked_pdfs: List[str] = Field(default_factory=list)
    detection_output_dir: Optional[str] = None


class ExtractRequest(BaseModel):
    run_id: str
    config_path: str = "config/config.yaml"


class PerturbRequest(BaseModel):
    run_id: str
    perturbation_json_path: Optional[str] = None
    mode: str = "existing"
    config_path: str = "config/config.yaml"
    input_dir: Optional[str] = None
    limit: Optional[int] = None
    force: bool = False


class InjectRequest(BaseModel):
    run_id: str
    methods: Optional[List[str]] = None
    compile_pdf: bool = True
    output_base_dir: Optional[str] = None
    config_path: str = "config/config.yaml"


class EvaluateRequest(BaseModel):
    run_id: str
    model: str = "gpt-4o"
    limit: Optional[int] = None
    method: Optional[str] = None
    config_path: str = "config/config.yaml"


app = FastAPI(title="IGSHIELD API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

RUN_STORE: Dict[str, RunContext] = {}


def _persist_run(ctx: RunContext) -> None:
    """Write run context to run_dir/context.json. Log errors but do not fail the request."""
    try:
        run_dir = RUNS_ROOT / ctx.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "context.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(ctx.model_dump(), f, indent=2, ensure_ascii=False)
    except OSError as e:
        logger.warning("Failed to persist run %s: %s", ctx.run_id, e)


def _load_persisted_runs() -> None:
    """Load all run contexts from backend/runs/run_*/context.json into RUN_STORE."""
    for path in RUNS_ROOT.glob("run_*/context.json"):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            ctx = RunContext.model_validate(data)
            RUN_STORE[ctx.run_id] = ctx
        except (OSError, json.JSONDecodeError, Exception) as e:
            logger.warning("Skip loading %s: %s", path, e)


_load_persisted_runs()


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path


def _load_config(config_path: str) -> Config:
    resolved = _resolve_path(config_path)
    config = Config.from_yaml(str(resolved))
    logger.info(
        "Loaded config from %s (mappings_per_question=%s)",
        resolved,
        config.processing.mappings_per_question,
    )
    return config


def _create_run_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"run_{stamp}_{uuid4().hex[:6]}"


def _get_run(run_id: str) -> RunContext:
    ctx = RUN_STORE.get(run_id)
    if not ctx:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return ctx


def _build_pdf_infos_from_run(ctx: RunContext, method_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build pdf_infos from run's attacked_pdfs and perturbation_jsons (upload run only)."""
    pdf_infos: List[Dict[str, Any]] = []
    if not ctx.attacked_pdfs or not ctx.perturbation_jsons:
        return pdf_infos
    json_path = _resolve_path(ctx.perturbation_jsons[0])
    if not json_path.exists():
        return pdf_infos
    for pdf_path_str in ctx.attacked_pdfs:
        pdf_path = _resolve_path(pdf_path_str)
        if not pdf_path.exists():
            continue
        parts = pdf_path.parts
        if "output_attacked_pdfs" not in parts:
            continue
        try:
            pdf_idx = parts.index("output_attacked_pdfs")
            if pdf_idx + 5 >= len(parts):
                continue
            timestamp = parts[pdf_idx + 1]
            domain = parts[pdf_idx + 2]
            level = parts[pdf_idx + 3]
            doc = parts[pdf_idx + 4]
            method = parts[pdf_idx + 5]
            if method_filter and method != method_filter:
                continue
            pdf_infos.append({
                "pdf": pdf_path,
                "json": json_path,
                "domain": domain,
                "level": level,
                "doc": doc,
                "method": method,
            })
        except (IndexError, ValueError):
            continue
    return pdf_infos


def _save_upload(upload: UploadFile, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)


def _find_perturbation_jsons(doc_name: str) -> List[Path]:
    pattern = f"{doc_name}_perturbation.json"
    base_dir = ROOT / "output_perturbation"
    if not base_dir.exists():
        return []
    candidates = list(base_dir.rglob(pattern))
    if not candidates:
        return []

    def sort_key(path: Path) -> str:
        parts = path.parts
        if "output_perturbation" in parts:
            idx = parts.index("output_perturbation")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return ""

    candidates.sort(key=sort_key, reverse=True)
    return candidates[:1]


def _attach_pdf_to_perturbation_json(source_json: Path, pdf_path: Optional[Path], dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with source_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if pdf_path:
        file_paths = data.get("file_paths")
        if not isinstance(file_paths, dict):
            file_paths = {}
        file_paths["pdf_file"] = str(pdf_path)
        data["file_paths"] = file_paths

    dest_path = dest_dir / source_json.name
    with dest_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return dest_path


def _count_perturbations(perturbation_json: Path) -> Dict[str, int]:
    with perturbation_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    doc = Document.model_validate(data)
    total_questions = len(doc.questions)
    total_perturbations = sum(len(q.perturbations) for q in doc.questions)
    return {"questions": total_questions, "perturbations": total_perturbations}


def _summarize_injection(results: Dict[str, Any]) -> Dict[str, Any]:
    methods = results.get("methods", {})
    compiled_pdfs = 0
    overlay_applied = 0
    pdf_paths: List[str] = []
    skipped_methods: List[str] = []
    failed_methods: List[str] = []
    for method_name, method_result in methods.items():
        if not method_result or not method_result.get("success"):
            # Injection failed; if there is compilation metadata, count as failed
            if method_result and method_result.get("pdf_compilation"):
                failed_methods.append(method_name)
            continue
        if "font_attack" in method_name:
            for pert_result in method_result.get("perturbations", []):
                pdf_comp = pert_result.get("pdf_compilation", {}) or {}
                if pdf_comp.get("success"):
                    compiled_pdfs += 1
                    if pert_result.get("pdf_path"):
                        pdf_paths.append(pert_result.get("pdf_path"))
        else:
            pdf_comp = method_result.get("pdf_compilation", {}) or {}
            if pdf_comp.get("success"):
                compiled_pdfs += 1
                if method_result.get("pdf_path"):
                    pdf_paths.append(method_result.get("pdf_path"))
            if method_result.get("dual_layer_applied"):
                overlay_applied += 1

        # Determine per-method skipped/failed status (only when nothing compiled for that method)
        if "font_attack" in method_name:
            perts = method_result.get("perturbations", []) or []
            had_success = any(
                (p.get("pdf_compilation") or {}).get("success") for p in perts
            )
            had_skipped = any(
                (p.get("pdf_compilation") or {}).get("skipped") for p in perts
            )
            had_failed = any(
                (p.get("pdf_compilation") or {}).get("success") is False
                and not (p.get("pdf_compilation") or {}).get("skipped")
                for p in perts
            )
            if not had_success:
                if had_skipped and not had_failed:
                    skipped_methods.append(method_name)
                elif had_failed:
                    failed_methods.append(method_name)
        else:
            if not method_result.get("pdf_compilation"):
                continue
            if method_result.get("pdf_compilation", {}).get("success"):
                continue
            if method_result.get("pdf_compilation", {}).get("skipped"):
                skipped_methods.append(method_name)
            else:
                failed_methods.append(method_name)

    return {
        "compiled_pdfs": compiled_pdfs,
        "overlay_applied": overlay_applied,
        "pdf_paths": pdf_paths,
        "skipped_compilation_methods": skipped_methods,
        "failed_compilation_methods": failed_methods,
    }


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/methods")
def list_methods(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    config = _load_config(config_path)
    return {"methods": config.injection.default_methods}


@app.post("/ingest")
async def ingest(
    pdf: Optional[UploadFile] = File(None),
    answer_key: Optional[UploadFile] = File(None),
    doc_name: Optional[str] = Form(None)
) -> Dict[str, Any]:
    run_id = _create_run_id()
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_ROOT / run_id
    upload_dir = run_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "input").mkdir(parents=True, exist_ok=True)
    (run_dir / "perturbations").mkdir(parents=True, exist_ok=True)

    pdf_path = None
    if pdf:
        pdf_path = upload_dir / pdf.filename
        _save_upload(pdf, pdf_path)

    answer_path = None
    if answer_key:
        answer_path = upload_dir / answer_key.filename
        _save_upload(answer_key, answer_path)

    resolved_doc_name = doc_name or (Path(pdf.filename).stem if pdf else "demo")

    ctx = RunContext(
        run_id=run_id,
        created_at=datetime.now().isoformat(),
        doc_name=resolved_doc_name,
        upload_dir=str(upload_dir),
        run_timestamp=run_timestamp,
        pdf_path=str(pdf_path) if pdf_path else None,
        answer_key_path=str(answer_path) if answer_path else None,
    )
    RUN_STORE[run_id] = ctx
    _persist_run(ctx)

    logger.info("Ingested run %s (doc_name=%s)", run_id, resolved_doc_name)
    return {
        "run_id": run_id,
        "doc_name": resolved_doc_name,
        "pdf_path": ctx.pdf_path,
        "answer_key_path": ctx.answer_key_path,
        "detail": "Upload complete"
    }


@app.post("/extract")
def extract(request: ExtractRequest) -> Dict[str, Any]:
    """Extract document (questions) from uploaded PDF via LLM and build LaTeX."""
    ctx = _get_run(request.run_id)
    if not ctx.pdf_path:
        raise HTTPException(status_code=400, detail="No PDF uploaded for this run. Call /ingest with a PDF first.")
    run_dir = RUNS_ROOT / ctx.run_id
    pdf_path = Path(ctx.pdf_path)
    if not pdf_path.is_absolute():
        pdf_path = ROOT / ctx.pdf_path
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF not found: {ctx.pdf_path}")
    answer_key_path = None
    if ctx.answer_key_path:
        answer_key_path = Path(ctx.answer_key_path)
        if not answer_key_path.is_absolute():
            answer_key_path = ROOT / ctx.answer_key_path
        if not answer_key_path.exists():
            answer_key_path = None
    doc_id = ctx.doc_name
    output_json_path = run_dir / "input" / f"{ctx.doc_name}.json"
    pdf_path_for_file_paths = pdf_path
    config = _load_config(request.config_path)
    input_dir = run_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    extract_images = getattr(config.processing, "extract_images", True) if config.processing else True
    max_images_first_page = getattr(config.processing, "max_images_first_page", 5) if config.processing else 5
    page_render_dpi = getattr(config.processing, "page_render_dpi", 200) if config.processing else 200
    doc = extract_document_from_pdf(
        pdf_path=pdf_path,
        answer_key_path=answer_key_path,
        doc_id=doc_id,
        output_json_path=output_json_path,
        pdf_path_for_file_paths=pdf_path_for_file_paths,
        config=config,
        output_dir=input_dir,
        extract_images=extract_images,
        max_images_first_page=max_images_first_page,
        page_render_dpi=page_render_dpi,
    )
    output_tex_path = run_dir / "input" / f"{ctx.doc_name}.tex"
    # Vision toggles
    vision_layout_enabled = False
    vision_template_enabled = False
    if config.processing:
        vision_layout_enabled = getattr(config.processing, "vision_layout_enabled", False) or getattr(
            config.processing, "vision_reconstructor_enabled", False
        )
        vision_template_enabled = getattr(config.processing, "vision_template_reconstruction_enabled", False)
    layout_json_path = None
    page_images = None
    if doc.file_paths:
        layout_json_path = getattr(doc.file_paths, "layout_json", None) or (
            doc.file_paths.get("layout_json") if isinstance(doc.file_paths, dict) else None
        )
        page_images = getattr(doc.file_paths, "page_images", None) or (
            doc.file_paths.get("page_images") if isinstance(doc.file_paths, dict) else None
        )
    # Prefer full template-based reconstruction when enabled; otherwise use heuristic + optional layout refinement
    if vision_template_enabled and layout_json_path and page_images:
        try:
            build_latex_with_vision_template(
                document=doc,
                layout_json_path=Path(layout_json_path),
                page_image_paths=page_images,
                config=config,
                output_tex_path=output_tex_path,
            )
        except Exception as e:
            logger.warning("Vision template reconstruction failed (%s); falling back to heuristic builder", e)
            # Optional layout refinement before heuristic LaTeX generation
            if vision_layout_enabled and layout_json_path and page_images:
                try:
                    doc = refine_layout_with_vision(
                        document=doc,
                        layout_json_path=Path(layout_json_path),
                        page_image_paths=page_images,
                        config=config,
                    )
                except Exception as le:
                    logger.warning("Vision layout refinement failed during fallback (%s); continuing with heuristic layout", le)
            build_latex_from_document(doc, output_tex_path)
    else:
        # Optional vision-assisted layout refinement
        if vision_layout_enabled and layout_json_path and page_images:
            try:
                doc = refine_layout_with_vision(
                    document=doc,
                    layout_json_path=Path(layout_json_path),
                    page_image_paths=page_images,
                    config=config,
                )
            except Exception as e:
                logger.warning("Vision layout refinement failed (%s); continuing with heuristic layout", e)

        # Heuristic LaTeX builder to generate .tex (template-driven and safe)
        build_latex_from_document(doc, output_tex_path)
    # Optional: overwrite with original LaTeX (and copy assets) when config points to a dir with {doc_id}.tex
    original_latex_dir = getattr(config.processing, "original_latex_dir", None) if config.processing else None
    if original_latex_dir and original_latex_dir.strip():
        base_dir = (ROOT / original_latex_dir.strip()).resolve()
        original_tex = base_dir / f"{doc_id}.tex"
        if original_tex.exists():
            shutil.copy(original_tex, output_tex_path)
            logger.info("Overwrote LaTeX with original from %s", original_tex)
            assets = getattr(config.processing, "original_latex_assets", None) or []
            input_dir = run_dir / "input"
            for name in assets:
                if not name or not isinstance(name, str):
                    continue
                src = base_dir / name
                if src.exists():
                    shutil.copy(src, input_dir / name)
                    logger.info("Copied asset %s to run input", name)
    ctx.document_json_path = str(output_json_path)
    RUN_STORE[ctx.run_id] = ctx
    _persist_run(ctx)
    logger.info("Extract complete for run %s: document_path=%s, latex_path=%s", request.run_id, output_json_path, output_tex_path)
    return {
        "run_id": ctx.run_id,
        "doc_name": ctx.doc_name,
        "document_path": str(output_json_path),
        "latex_path": str(output_tex_path),
        "detail": f"Extracted {len(doc.questions)} questions and built LaTeX"
    }


@app.post("/perturb")
def perturb(request: PerturbRequest) -> Dict[str, Any]:
    ctx = _get_run(request.run_id)
    run_dir = RUNS_ROOT / ctx.run_id
    attached_dir = run_dir / "perturbations"
    attached_jsons: List[str] = []

    # Single-document path: extract produced document JSON under run_dir
    if ctx.document_json_path:
        doc_json_path = Path(ctx.document_json_path)
        if not doc_json_path.is_absolute():
            doc_json_path = ROOT / ctx.document_json_path
        if not doc_json_path.exists():
            raise HTTPException(status_code=404, detail=f"Document JSON not found: {ctx.document_json_path}")
        config = _load_config(request.config_path)
        processor = Processor(config)
        run_latex_path = None
        with doc_json_path.open("r", encoding="utf-8") as f:
            doc_data = json.load(f)
        fp = doc_data.get("file_paths") or {}
        if isinstance(fp, dict) and fp.get("latex_file"):
            run_latex_path = Path(fp["latex_file"])
        elif hasattr(fp, "latex_file") and getattr(fp, "latex_file", None):
            run_latex_path = Path(getattr(fp, "latex_file"))
        run_pdf_path = Path(ctx.pdf_path) if ctx.pdf_path else None
        output_path = processor.process_single_document(
            json_path=doc_json_path,
            output_dir=attached_dir,
            run_pdf_path=run_pdf_path,
            run_latex_path=run_latex_path,
            mode="immediate",
        )
        if not output_path:
            raise HTTPException(status_code=500, detail="Single-document perturbation generation failed")
        attached_jsons = [str(output_path)]
        ctx.perturbation_jsons = attached_jsons
        RUN_STORE[ctx.run_id] = ctx
        _persist_run(ctx)
        stats = _count_perturbations(output_path)
        detail = f"Generated {stats['perturbations']} perturbations for {stats['questions']} questions"
        logger.info("Perturbations ready for run %s (single-doc)", request.run_id)
        return {
            "run_id": ctx.run_id,
            "perturbation_jsons": attached_jsons,
            "count": len(attached_jsons),
            "stats": stats,
            "detail": detail,
        }

    # Existing path: find or generate from output_perturbation, then attach to run
    if request.mode == "generate":
        config = _load_config(request.config_path)
        if request.input_dir:
            config.processing.input_dir = request.input_dir
        processor = Processor(config)
        logger.info("Generating perturbations for run %s", request.run_id)
        processor.process_all_files(limit=request.limit, force=request.force, mode="immediate")

    if request.perturbation_json_path:
        candidate = _resolve_path(request.perturbation_json_path)
        if not candidate.exists():
            raise HTTPException(status_code=404, detail=f"Perturbation JSON not found: {candidate}")
        json_paths = [candidate]
    else:
        json_paths = _find_perturbation_jsons(ctx.doc_name)
        if not json_paths:
            config = _load_config(request.config_path)
            logger.info("No perturbations found for %s. Generating now.", ctx.doc_name)
            processor = Processor(config)
            processor.process_all_files(limit=request.limit, force=request.force, mode="immediate")
            json_paths = _find_perturbation_jsons(ctx.doc_name)

    if not json_paths:
        raise HTTPException(status_code=404, detail=f"No perturbation JSONs found for doc '{ctx.doc_name}'")

    for json_path in json_paths:
        attached = _attach_pdf_to_perturbation_json(
            json_path,
            Path(ctx.pdf_path) if ctx.pdf_path else None,
            attached_dir,
        )
        attached_jsons.append(str(attached))

    ctx.perturbation_jsons = attached_jsons
    RUN_STORE[ctx.run_id] = ctx
    _persist_run(ctx)

    stats = _count_perturbations(Path(attached_jsons[0]))
    detail = f"Loaded {stats['perturbations']} perturbations"
    if stats["perturbations"] == 0:
        detail = "Loaded 0 perturbations (check the JSON contents)"

    logger.info("Perturbations ready for run %s", request.run_id)
    return {
        "run_id": ctx.run_id,
        "perturbation_jsons": attached_jsons,
        "count": len(attached_jsons),
        "stats": stats,
        "detail": detail
    }


@app.post("/inject")
def inject(request: InjectRequest) -> Dict[str, Any]:
    ctx = _get_run(request.run_id)

    if not ctx.perturbation_jsons:
        raise HTTPException(status_code=400, detail="No perturbation JSONs found for this run. Call /perturb first.")

    config = _load_config(request.config_path)
    if request.output_base_dir:
        config.pdf_generation.output_base_dir = request.output_base_dir

    methods = request.methods or config.injection.default_methods
    # Capture compilation intent and whether config allows it
    compile_pdf_requested = bool(request.compile_pdf)
    compile_pdf_enabled = bool(
        getattr(getattr(config, "pdf_generation", None), "compile_pdf", True)
    )
    compile_pdf_effective = bool(compile_pdf_requested and compile_pdf_enabled)
    run_timestamp = ctx.run_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")

    generator = OrganizedPDFGenerator(
        config=config, base_output_dir=Path(config.pdf_generation.output_base_dir)
    )

    all_results = []
    for json_path in ctx.perturbation_jsons:
        result = generator.process_document(
            perturbation_json_path=Path(json_path),
            methods=methods,
            run_timestamp=run_timestamp,
            compile_pdf=request.compile_pdf,
        )
        all_results.append(result)

    artifacts = []
    summary = {"compiled_pdfs": 0, "overlay_applied": 0, "pdf_paths": []}
    for result in all_results:
        method_summary = _summarize_injection(result)
        summary["compiled_pdfs"] += method_summary["compiled_pdfs"]
        summary["overlay_applied"] += method_summary["overlay_applied"]
        summary["pdf_paths"].extend(method_summary["pdf_paths"])

    for pdf_path in summary["pdf_paths"]:
        artifacts.append({"label": "Attacked PDF", "value": pdf_path})

    ctx.attacked_output_dir = config.pdf_generation.output_base_dir
    ctx.attacked_pdfs = summary["pdf_paths"]
    RUN_STORE[ctx.run_id] = ctx
    _persist_run(ctx)

    if summary["compiled_pdfs"] == 0 and not compile_pdf_effective:
        logger.warning(
            "Injection succeeded for run %s but no PDFs were compiled "
            "(compile_pdf_requested=%s, compile_pdf_enabled=%s)",
            request.run_id,
            compile_pdf_requested,
            compile_pdf_enabled,
        )

    logger.info("Injection complete for run %s", request.run_id)
    return {
        "run_id": ctx.run_id,
        "methods": methods,
        "results": all_results,
        "summary": summary,
        "artifacts": artifacts,
        "compile_pdf_requested": compile_pdf_requested,
        "compile_pdf_enabled": compile_pdf_enabled,
        "compile_pdf_effective": compile_pdf_effective,
        "detail": f"Compiled {summary['compiled_pdfs']} PDFs",
    }


@app.post("/evaluate")
def evaluate(request: EvaluateRequest) -> Dict[str, Any]:
    ctx = _get_run(request.run_id)

    config = _load_config(request.config_path)

    if ctx.run_timestamp and ctx.attacked_pdfs:
        pdf_infos = _build_pdf_infos_from_run(ctx, method_filter=request.method)
        if not pdf_infos:
            raise HTTPException(
                status_code=404,
                detail="No attacked PDFs found for this run. Run inject first, or no PDFs match the method filter.",
            )
    else:
        output_base = Path(ctx.attacked_output_dir or config.pdf_generation.output_base_dir)
        if not output_base.exists():
            raise HTTPException(status_code=404, detail=f"Output PDFs not found at {output_base}")
        pdf_infos = find_perturbed_pdfs(output_base, method_filter=request.method)
        if not pdf_infos:
            raise HTTPException(status_code=404, detail="No attacked PDFs found for evaluation")

    if request.limit:
        pdf_infos = pdf_infos[:request.limit]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = RUNS_ROOT / ctx.run_id / "detection" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    collector = ResponseCollector(config, model=request.model)
    matcher = SignatureMatcher()
    calculator = MetricsCalculator()

    detection_results: List[Dict[str, Any]] = []

    for pdf_info in pdf_infos:
        pdf_path = pdf_info["pdf"]
        json_path = pdf_info["json"]
        doc_output_dir = output_dir / pdf_info["doc"]
        response_data = collector.collect_responses(pdf_path, json_path, doc_output_dir)

        with open(json_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
        doc = Document.model_validate(doc_data)

        for response in response_data["responses"].values():
            q_num = response["question_number"]
            question = next((q for q in doc.questions if q.question_number == q_num), None)
            if not question:
                continue
            match_result = matcher.match_response(response, question)
            match_result["question_number"] = q_num
            match_result["question_type"] = response["question_type"]
            if "parsing_method" in response:
                match_result["parsing_method"] = response["parsing_method"]
            detection_results.append(match_result)

    metrics = calculator.calculate_metrics(detection_results, output_dir)
    report_path = calculator.generate_report(metrics, detection_results, output_dir)

    ctx.detection_output_dir = str(output_dir)
    RUN_STORE[ctx.run_id] = ctx
    _persist_run(ctx)

    logger.info("Evaluation complete for run %s", request.run_id)
    return {
        "run_id": ctx.run_id,
        "metrics": metrics,
        "sample_results": detection_results[:20],
        "report_path": str(report_path),
        "output_dir": str(output_dir),
        "detail": "Evaluation complete"
    }


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> Dict[str, Any]:
    ctx = _get_run(run_id)
    return ctx.model_dump()


@app.get("/runs/{run_id}/artifacts/{filename}")
def get_run_artifact(run_id: str, filename: str):
    """Serve a PDF artifact for a run. Only paths in the run's attacked_pdfs are allowed."""
    ctx = _get_run(run_id)
    if not ctx.attacked_pdfs:
        raise HTTPException(status_code=404, detail="No artifacts for this run")
    path_str = None
    for p in ctx.attacked_pdfs:
        if Path(p).name == filename:
            path_str = p
            break
    if not path_str:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {filename}")
    path = _resolve_path(path_str)
    path = path.resolve()
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    root_resolved = ROOT.resolve()
    try:
        if not path.is_relative_to(root_resolved):
            raise HTTPException(status_code=403, detail="Access denied")
    except AttributeError:
        root_parts = root_resolved.parts
        path_parts = path.parts
        if path_parts[: len(root_parts)] != root_parts:
            raise HTTPException(status_code=403, detail="Access denied")
    response = FileResponse(path, media_type="application/pdf")
    response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    return response
