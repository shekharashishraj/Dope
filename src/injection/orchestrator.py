"""Orchestrator for applying injection methods and compiling PDFs."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Optional
from pydantic import ValidationError
from .icw_injector import ICWInjector
from .dual_layer_injector import DualLayerInjector
from .font_attack_injector import FontAttackInjector
from .hybrid_injectors import ICWDualLayerInjector, ICWFontAttackInjector
from ..models.perturbation import Document


class InjectionOrchestrator:
    """Orchestrates injection methods and PDF compilation."""
    
    INJECTION_METHODS = {
        "icw": ICWInjector,
        "dual_layer": DualLayerInjector,
        "font_attack": FontAttackInjector,
        "icw_dual_layer": ICWDualLayerInjector,
        "icw_font_attack": ICWFontAttackInjector,
    }
    
    def __init__(self, output_dir: Path = None, config=None):
        """
        Initialize orchestrator.
        
        Args:
            output_dir: Base output directory for generated files
            config: Configuration object (optional)
        """
        self.output_dir = output_dir or Path("output")
        self.config = config
    
    def process_document(
        self,
        perturbation_json_path: Path,
        methods: List[str] = None,
        compile_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Process a document with specified injection methods.
        
        Args:
            perturbation_json_path: Path to perturbation JSON file
            methods: List of methods to apply (default: all methods)
            compile_pdf: Whether to compile LaTeX to PDF
        
        Returns:
            Dictionary with results for each method
        """
        if methods is None:
            # Use default methods from config if available
            if self.config:
                methods = [m for m in self.config.injection.default_methods if m in self.config.injection.methods and self.config.injection.methods[m].enabled]
            else:
                methods = list(self.INJECTION_METHODS.keys())
        
        # Load perturbation data as Document model
        with open(perturbation_json_path, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)
        
        try:
            data = Document.model_validate(data_dict)
        except ValidationError as e:
            # Log warning but try to continue
            print(f"Warning: Validation errors in {perturbation_json_path}: {e}")
            data = Document.model_validate(data_dict)  # Will use extra='allow'
        
        # Get LaTeX file path
        latex_path_str = None
        if data.file_paths and data.file_paths.latex_file:
            latex_path_str = data.file_paths.latex_file
        if not latex_path_str:
            raise ValueError(f"No LaTeX file path found in {perturbation_json_path}")
        
        # Handle Windows/Unix path separators
        latex_path_str = latex_path_str.replace('\\', '/')
        latex_path = self.output_dir.parent / latex_path_str if self.output_dir else Path(latex_path_str)
        
        if not latex_path.exists():
            raise FileNotFoundError(f"LaTeX file not found: {latex_path}")
        
        # Read LaTeX content
        try:
            tex_content = latex_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            tex_content = latex_path.read_text(encoding='latin-1')
        
        # Extract questions and perturbations
        questions = data.questions
        all_perturbations = []
        for q in questions:
            all_perturbations.extend(q.perturbations)
        
        # Process each method
        results = {}
        docid = data.docid or 'unknown'
        
        for method_name in methods:
            if method_name not in self.INJECTION_METHODS:
                results[method_name] = {
                    "success": False,
                    "error": f"Unknown method: {method_name}"
                }
                continue
            
            try:
                # For font attack methods, generate separate PDFs for each perturbation (1, 2, 3)
                if "font_attack" in method_name:
                    # Process each perturbation separately
                    perturbation_results = []
                    
                    for pert_idx in range(1, 4):  # 1, 2, 3
                        print(f"[Orchestrator] Processing {method_name} with perturbation {pert_idx}...")
                        
                        # Filter perturbations to only include the pert_idx-th one for each question
                        filtered_perturbations = []
                        filtered_questions = []
                        from ..models.perturbation import Question
                        
                        for q in questions:
                            q_perturbations = q.perturbations
                            if len(q_perturbations) >= pert_idx:
                                # Create a new Question with only this perturbation
                                q_copy = Question(
                                    question_number=q.question_number,
                                    question_type=q.question_type,
                                    stem_text=q.stem_text,
                                    options=q.options,
                                    gold_answer=q.gold_answer,
                                    perturbations=[q_perturbations[pert_idx - 1]],  # 0-indexed
                                    latex_stem_text=q.latex_stem_text
                                )
                                filtered_questions.append(q_copy)
                                filtered_perturbations.append(q_perturbations[pert_idx - 1])
                        
                        if not filtered_questions:
                            print(f"[Orchestrator] No perturbations found for index {pert_idx}, skipping")
                            continue
                        
                        # Initialize injector
                        print(f"[Orchestrator] Initializing {method_name} injector for perturbation {pert_idx}...")
                        injector_class = self.INJECTION_METHODS[method_name]
                        # Pass config to injector if it accepts it
                        try:
                            injector = injector_class(config=self.config)
                        except TypeError:
                            # Injector doesn't accept config parameter, use default
                            try:
                                injector = injector_class()
                            except Exception as e:
                                print(f"[Orchestrator] ERROR: Failed to initialize {method_name} injector: {e}")
                                continue
                        except Exception as e:
                            print(f"[Orchestrator] ERROR: Failed to initialize {method_name} injector: {e}")
                            continue
                        print(f"[Orchestrator] {method_name} injector initialized")
                        
                        # Apply injection with filtered perturbations
                        print(f"[Orchestrator] Applying {method_name} injection for perturbation {pert_idx}...")
                        modified_tex, metadata = injector.inject(
                            tex_content, filtered_perturbations, filtered_questions
                        )
                        print(f"[Orchestrator] {method_name} injection complete for perturbation {pert_idx}")
                        
                        # Save modified LaTeX with suffix
                        output_base = self._get_output_path(perturbation_json_path, method_name)
                        output_base = output_base.parent / f"{output_base.name}_{pert_idx}font"
                        output_base.parent.mkdir(parents=True, exist_ok=True)
                        modified_tex_path = output_base.with_suffix('.tex')
                        modified_tex_path.write_text(modified_tex, encoding='utf-8')
                        
                        # Generate fonts
                        fonts_dir = None
                        if hasattr(injector, 'generate_fonts'):
                            print(f"[Orchestrator] Generating fonts for {method_name} perturbation {pert_idx}")
                            fonts_dir = output_base.parent / f"fonts_{pert_idx}"
                            fonts_dir.mkdir(parents=True, exist_ok=True)
                            print(f"[Orchestrator] Fonts directory: {fonts_dir}")
                            generated_fonts = injector.generate_fonts(fonts_dir)
                            print(f"[Orchestrator] Generated {len(generated_fonts)} font files")
                        
                        pert_result = {
                            "success": True,
                            "method": method_name,
                            "perturbation_index": pert_idx,
                            "modified_tex_path": str(modified_tex_path),
                            "metadata": metadata
                        }
                        if fonts_dir:
                            pert_result["fonts_dir"] = str(fonts_dir)
                            pert_result["fonts_generated"] = len(generated_fonts) if "generated_fonts" in locals() else 0
                        
                        # Compile PDF if requested
                        if compile_pdf and (not self.config or self.config.pdf_generation.compile_pdf):
                            require_xetex = self.config.pdf_generation.require_xetex_for_fonts if self.config else True  # Font attack always uses XeTeX
                            compilation_timeout = self.config.pdf_generation.compilation_timeout if self.config else 300
                            pdf_result = self._compile_pdf(
                                modified_tex_path,
                                latex_path.parent,
                                output_base.with_suffix('.pdf'),
                                require_xetex=require_xetex,
                                fonts_dir=fonts_dir,
                                timeout=compilation_timeout
                            )
                            pert_result["pdf_compilation"] = pdf_result
                            if pdf_result.get("success"):
                                compiled_pdf = output_base.with_suffix('.pdf')
                                pert_result["pdf_path"] = str(compiled_pdf)
                                
                                # Clean up malicious fonts after successful PDF compilation
                                cleanup_fonts = self.config.pdf_generation.cleanup_fonts_after_compile if self.config else True
                                if fonts_dir and fonts_dir.exists() and cleanup_fonts:
                                    self._cleanup_fonts(fonts_dir)
                                    pert_result["fonts_cleaned"] = True
                        
                        perturbation_results.append(pert_result)
                    
                    # Combine results
                    if len(perturbation_results) == 0:
                        # No perturbations were generated - this is a failure case
                        print(f"[Orchestrator] WARNING: {method_name} - No perturbations found for any index (1, 2, 3)")
                        print(f"[Orchestrator] This usually means the perturbation JSON has no perturbations for any questions")
                        result = {
                            "success": False,
                            "method": method_name,
                            "error": "No perturbations found in document - all questions have empty perturbations arrays",
                            "perturbations": [],
                            "total_perturbations": 0
                        }
                    else:
                        result = {
                            "success": True,
                            "method": method_name,
                            "perturbations": perturbation_results,
                            "total_perturbations": len(perturbation_results)
                        }
                else:
                    # Non-font-attack methods: process all perturbations together
                    # Initialize injector
                    print(f"[Orchestrator] Initializing {method_name} injector...")
                    injector_class = self.INJECTION_METHODS[method_name]
                    # Pass config to injector if it accepts it
                    try:
                        injector = injector_class(config=self.config)
                    except TypeError:
                        # Injector doesn't accept config parameter, use default
                        try:
                            injector = injector_class()
                        except Exception as e:
                            print(f"[Orchestrator] ERROR: Failed to initialize {method_name} injector: {e}")
                            result = {"success": False, "method": method_name, "error": str(e)}
                            continue
                    except Exception as e:
                        print(f"[Orchestrator] ERROR: Failed to initialize {method_name} injector: {e}")
                        result = {"success": False, "method": method_name, "error": str(e)}
                        continue
                    print(f"[Orchestrator] {method_name} injector initialized")
                    
                    # Apply injection
                    print(f"[Orchestrator] Applying {method_name} injection...")
                    modified_tex, metadata = injector.inject(
                        tex_content, all_perturbations, questions
                    )
                    print(f"[Orchestrator] {method_name} injection complete")
                    
                    # Save modified LaTeX
                    output_base = self._get_output_path(perturbation_json_path, method_name)
                    output_base.parent.mkdir(parents=True, exist_ok=True)
                    modified_tex_path = output_base.with_suffix('.tex')
                    modified_tex_path.write_text(modified_tex, encoding='utf-8')
                    
                    result = {
                        "success": True,
                        "method": method_name,
                        "modified_tex_path": str(modified_tex_path),
                        "metadata": metadata
                    }
                    
                    # Compile PDF if requested
                    if compile_pdf:
                        require_xetex = "font_attack" in method_name
                        pdf_result = self._compile_pdf(
                            modified_tex_path,
                            latex_path.parent,
                            output_base.with_suffix('.pdf'),
                            require_xetex=require_xetex
                        )
                        result["pdf_compilation"] = pdf_result
                        if pdf_result.get("success"):
                            compiled_pdf = output_base.with_suffix('.pdf')
                            result["pdf_path"] = str(compiled_pdf)
                            
                            # Apply PDF-level dual-layer image overlay if needed
                            apply_overlay = self.config.pdf_generation.apply_pdf_overlay if self.config else True
                            if apply_overlay and "dual_layer" in method_name and "font_attack" not in method_name:
                                from .pdf_overlay_dual_layer import apply_image_overlay_dual_layer
                                final_pdf = output_base.parent / f"{output_base.name}_final.pdf"
                                
                                # Build mappings with geometry info
                                mappings = []
                                for q in questions:
                                    for p in q.perturbations:
                                        if p.original_substring and p.replacement_substring:
                                            # Try to get geometry from perturbation
                                            mapping = {
                                                'original': p.original_substring,
                                                'replacement': p.replacement_substring,
                                                'page_index': getattr(p, 'page_index', None),  # Will be determined from PDF search
                                                'bbox': getattr(p, 'bbox', None),
                                                'selection_rect': getattr(p, 'selection_rect', None)
                                            }
                                            # Add any geometry info if available (from extra fields)
                                            p_dict = p.model_dump()
                                            if 'bbox' in p_dict:
                                                mapping['bbox'] = p_dict['bbox']
                                            if 'selection_rect' in p_dict:
                                                mapping['selection_rect'] = p_dict['selection_rect']
                                            if 'page_index' in p_dict:
                                                mapping['page_index'] = p_dict['page_index']
                                            mappings.append(mapping)
                                
                                # Find original PDF from perturbation JSON file_paths
                                print(f"[Orchestrator] Searching for original PDF for dual layer overlay...")
                                original_pdf = None
                                if data.file_paths:
                                    # Check for pdf_file in extra fields (not in model)
                                    data_dict = data.model_dump()
                                    if 'file_paths' in data_dict and isinstance(data_dict['file_paths'], dict):
                                        pdf_path_str = data_dict['file_paths'].get('pdf_file', '')
                                    else:
                                        pdf_path_str = ''
                                    if pdf_path_str:
                                        # Handle Windows/Unix path separators
                                        pdf_path_str = pdf_path_str.replace('\\', '/')
                                        original_pdf = Path(pdf_path_str)
                                        if not original_pdf.is_absolute():
                                            # Resolve relative to output directory
                                            original_pdf = self.output_dir.parent / pdf_path_str
                                        print(f"[Orchestrator] Original PDF from file_paths: {original_pdf} (exists: {original_pdf.exists()})")
                                
                                # Fallback: try common locations
                                search_original = self.config.pdf_generation.overlay_search_original_pdf if self.config else True
                                if search_original and (not original_pdf or not original_pdf.exists()):
                                    # Try pdf_documents folder
                                    base_name = latex_path.stem
                                    # Remove method suffixes
                                    for suffix in ['_icw', '_dual_layer', '_font_attack', '_icw_dual_layer', '_icw_font_attack']:
                                        base_name = base_name.replace(suffix, '')
                                    
                                    pdf_dir = latex_path.parent.parent / "pdf_documents"
                                    original_pdf = pdf_dir / f"{base_name}.pdf"
                                    print(f"[Orchestrator] Trying pdf_documents folder: {original_pdf} (exists: {original_pdf.exists()})")
                                
                                # Last fallback: use compiled PDF (will still work but less effective)
                                if not original_pdf or not original_pdf.exists():
                                    print(f"[Orchestrator] WARNING: Original PDF not found! Will use compiled PDF as fallback.")
                                    print(f"[Orchestrator] This means the overlay will show replacement text instead of original.")
                                    original_pdf = None
                                else:
                                    print(f"[Orchestrator] ✓ Original PDF found: {original_pdf}")
                                
                                print(f"[Orchestrator] Applying dual layer overlay with {len(mappings)} mappings...")
                                if apply_image_overlay_dual_layer(
                                    original_pdf_path=original_pdf if original_pdf and original_pdf.exists() else None,
                                    compiled_pdf_path=compiled_pdf,
                                    output_pdf_path=final_pdf,
                                    mappings=mappings,
                                    search_pdf_path=compiled_pdf  # Fallback to compiled PDF
                                ):
                                    result["pdf_path"] = str(final_pdf)
                                    result["dual_layer_applied"] = True
                                    result["overlay_method"] = "image_overlay"
                                    result["original_pdf_used"] = str(original_pdf) if original_pdf else "fallback (compiled PDF)"
                                    print(f"[Orchestrator] ✓ Dual layer overlay applied successfully")
                                else:
                                    print(f"[Orchestrator] ✗ Dual layer overlay failed")
                                    result["overlay_error"] = "Overlay application failed"
                
                results[method_name] = result
                
            except Exception as e:
                results[method_name] = {
                    "success": False,
                    "error": str(e),
                    "method": method_name
                }
        
        return {
            "docid": docid,
            "source_latex": str(latex_path),
            "source_json": str(perturbation_json_path),
            "methods": results
        }
    
    def _get_output_path(self, perturbation_json_path: Path, method_name: str) -> Path:
        """Get output path for modified LaTeX/PDF."""
        # Extract document info from path
        # e.g., output/astronomy/graduate/JSON_output_perturbation/astronomy_graduate_doc_01_perturbation.json
        parts = perturbation_json_path.parts
        
        # Find the subject and level
        subject_idx = None
        level_idx = None
        
        for i, part in enumerate(parts):
            if part == "output" and i + 1 < len(parts):
                subject_idx = i + 1
            if subject_idx and i == subject_idx + 1:
                level_idx = i
        
        if subject_idx and level_idx:
            subject = parts[subject_idx]
            level = parts[level_idx]
            doc_name = perturbation_json_path.stem.replace('_perturbation', '')
            
            # Create output directory: output/subject/level/injected_{method}/
            output_dir = self.output_dir / subject / level / f"injected_{method_name}"
            return output_dir / f"{doc_name}_{method_name}"
        else:
            # Fallback
            output_dir = perturbation_json_path.parent / f"injected_{method_name}"
            return output_dir / f"{perturbation_json_path.stem}_{method_name}"
    
    def _compile_pdf(
        self,
        tex_path: Path,
        assets_dir: Path,
        output_pdf: Path,
        require_xetex: bool = False,
        fonts_dir: Optional[Path] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Compile LaTeX to PDF.
        
        Args:
            tex_path: Path to LaTeX file
            assets_dir: Directory containing assets (images, etc.)
            output_pdf: Output PDF path
        
        Returns:
            Compilation result dictionary
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="latex_compile_"))
        compile_log = output_pdf.parent / f"{output_pdf.stem}_compile.log"
        
        try:
            # Copy LaTeX file to temp directory
            working_tex = temp_dir / "document.tex"
            shutil.copy2(tex_path, working_tex)
            
            # Copy assets if they exist
            if assets_dir.exists():
                for item in assets_dir.iterdir():
                    if item.is_file() and item.suffix in ['.png', '.jpg', '.jpeg', '.pdf']:
                        shutil.copy2(item, temp_dir / item.name)
            
            # Copy fonts directory if provided (for font attack methods)
            if fonts_dir and fonts_dir.exists():
                print(f"[Orchestrator] Copying fonts from {fonts_dir} to {temp_dir}/fonts")
                temp_fonts_dir = temp_dir / "fonts"
                if fonts_dir.is_dir():
                    # Copy entire fonts directory structure
                    shutil.copytree(fonts_dir, temp_fonts_dir, dirs_exist_ok=True)
                    print(f"[Orchestrator] Copied fonts directory structure")
                elif fonts_dir.is_file():
                    # Single font file
                    temp_fonts_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(fonts_dir, temp_fonts_dir / fonts_dir.name)
                    print(f"[Orchestrator] Copied single font file")
            
            # Compile with appropriate compiler
            # Use config to determine compiler preference
            compiler_pref = self.config.pdf_generation.latex_compiler if self.config else "auto"
            
            if require_xetex:
                compilers = ['xelatex']
            elif compiler_pref == "xelatex":
                compilers = ['xelatex']
            elif compiler_pref == "pdflatex":
                compilers = ['pdflatex']
            elif compiler_pref == "lualatex":
                compilers = ['lualatex']
            else:
                # Auto: try xelatex first, then pdflatex
                compilers = ['xelatex', 'pdflatex']
            
            success = False
            error_msg = None
            
            for compiler in compilers:
                try:
                    proc = subprocess.run(
                        [compiler, "-interaction=nonstopmode", "document.tex"],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                    
                    log_content = f"Compiler: {compiler}\n"
                    log_content += f"Return code: {proc.returncode}\n"
                    log_content += f"STDOUT:\n{proc.stdout}\n"
                    log_content += f"STDERR:\n{proc.stderr}\n"
                    
                    compile_log.write_text(log_content, encoding='utf-8')
                    
                    compiled_pdf = temp_dir / "document.pdf"
                    if proc.returncode == 0 and compiled_pdf.exists():
                        output_pdf.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(compiled_pdf, output_pdf)
                        success = True
                        break
                    else:
                        error_msg = f"{compiler} compilation failed"
                except FileNotFoundError:
                    error_msg = f"{compiler} not found"
                    continue
                except subprocess.TimeoutExpired:
                    error_msg = f"{compiler} compilation timed out"
                    continue
            
            return {
                "success": success,
                "error": error_msg,
                "log_path": str(compile_log)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "log_path": str(compile_log)
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _cleanup_fonts(self, fonts_dir: Path) -> None:
        """
        Delete malicious fonts directory after successful PDF compilation.
        
        Args:
            fonts_dir: Path to the fonts directory to delete
        """
        try:
            if fonts_dir.exists():
                print(f"[Orchestrator] Cleaning up fonts directory: {fonts_dir}")
                shutil.rmtree(fonts_dir, ignore_errors=True)
                print(f"[Orchestrator] Successfully deleted fonts directory: {fonts_dir}")
            else:
                print(f"[Orchestrator] Fonts directory does not exist: {fonts_dir}")
        except Exception as e:
            print(f"[Orchestrator] Warning: Failed to cleanup fonts directory {fonts_dir}: {e}")

