"""Command-line script to generate attacked PDFs from perturbation JSON files."""
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz
from logging.handlers import RotatingFileHandler
from .injection.orchestrator import InjectionOrchestrator
from .config import Config

def get_timezone(config):
    """Get timezone from config."""
    timezone_str = config.logging.timezone if config else "America/Denver"
    return pytz.timezone(timezone_str)

class MSTFormatter(logging.Formatter):
    """Custom formatter that converts time to configured timezone."""
    def __init__(self, fmt=None, datefmt=None, config=None):
        super().__init__(fmt, datefmt)
        self.config = config
    
    def formatTime(self, record, datefmt=None):
        tz = get_timezone(self.config)
        dt = datetime.fromtimestamp(record.created, tz=tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S %Z')

def setup_logging(config=None, log_dir: Path = None):
    """Set up detailed logging with configured timezone and file output."""
    if not config or not config.logging.enabled:
        # Basic logging if disabled or no config
        logging.basicConfig(level=logging.INFO)
        return None
    
    if log_dir is None:
        log_dir = Path(config.logging.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get timezone
    tz = get_timezone(config)
    
    # Create log filename with timestamp
    timestamp = datetime.now(tz).strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"pdf_generation_{timestamp}.log"
    
    # Create formatter with configured timezone
    formatter = MSTFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z',
        config=config
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.logging.max_bytes,
        backupCount=config.logging.backup_count
    )
    file_level = getattr(logging, config.logging.file_level.upper(), logging.DEBUG)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_level = getattr(logging, config.logging.console_level.upper(), logging.INFO)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    root_logger.setLevel(root_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return log_file

# Initialize logging will be done after Config is loaded
log_file = None
logger = logging.getLogger(__name__)


def extract_metadata_from_json(perturbation_json_path: Path) -> Dict[str, str]:
    """
    Extract metadata (subject, level, document_name) from perturbation JSON.
    
    Args:
        perturbation_json_path: Path to perturbation JSON file
    
    Returns:
        Dictionary with subject, level, and document_name
    """
    try:
        from .models.perturbation import Document
        from pydantic import ValidationError
        
        with open(perturbation_json_path, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)
        
        try:
            data = Document.model_validate(data_dict)
        except ValidationError:
            # Fallback to dict access if validation fails
            data = None
        
        # Try to extract from JSON metadata
        if data:
            subject = data.domain or ''
            level = data.academic_level or ''
            docid = data.docid or ''
        else:
            subject = data_dict.get('domain', data_dict.get('subject', ''))
            level = data_dict.get('academic_level', data_dict.get('level', ''))
            docid = data_dict.get('docid', '')
        
        document_name = docid  # Use docid as document_name
        
        # If not in JSON, try to extract from path
        if not subject or not level:
            # Try to parse from path: output_perturbation/timestamp/subject/level/question_paper_name/file.json
            parts = perturbation_json_path.parts
            try:
                # Look for output_perturbation in path
                if 'output_perturbation' in parts:
                    idx = parts.index('output_perturbation')
                    if idx + 3 < len(parts):
                        # Skip timestamp, get subject and level
                        subject = parts[idx + 2] if not subject else subject
                        level = parts[idx + 3] if not level else level
            except (ValueError, IndexError):
                pass
        
        # Use docid or document_name, fallback to filename
        if not document_name:
            if docid:
                document_name = docid
            else:
                # Extract from filename: cybersecurity_undergraduate_doc_01_perturbation.json
                document_name = perturbation_json_path.stem.replace('_perturbation', '')
        
        return {
            'subject': subject or 'unknown',
            'level': level or 'unknown',
            'document_name': document_name or perturbation_json_path.stem.replace('_perturbation', '')
        }
    except Exception as e:
        logger.warning(f"Failed to extract metadata from {perturbation_json_path}: {e}")
        # Fallback: use filename
        stem = perturbation_json_path.stem.replace('_perturbation', '')
        return {
            'subject': 'unknown',
            'level': 'unknown',
            'document_name': stem
        }


def find_perturbation_files(perturbation_folder: Path) -> List[Path]:
    """
    Find all perturbation JSON files in the given folder (recursively).
    
    Args:
        perturbation_folder: Path to folder containing perturbation JSON files
        
    Returns:
        List of Path objects to perturbation JSON files
    """
    if not perturbation_folder.exists():
        raise FileNotFoundError(f"Perturbation folder does not exist: {perturbation_folder}")
    
    json_files = list(perturbation_folder.rglob("*_perturbation.json"))
    
    if not json_files:
        # Also try without _perturbation suffix
        json_files = list(perturbation_folder.rglob("*.json"))
        # Filter out batch_info.json and other non-perturbation files
        json_files = [f for f in json_files if 'batch_info' not in f.name and 'batch' not in f.name.lower()]
    
    return sorted(json_files)


class OrganizedPDFGenerator:
    """PDF generator with organized output structure."""
    
    def __init__(self, config: Config, base_output_dir: Path = None):
        """
        Initialize PDF generator.
        
        Args:
            config: Configuration object
            base_output_dir: Base output directory (default: from config)
        """
        self.config = config
        if base_output_dir is None:
            base_output_dir = Path(config.pdf_generation.output_base_dir)
        self.base_output_dir = base_output_dir
        self.orchestrator = InjectionOrchestrator(output_dir=base_output_dir, config=config)
    
    def _get_organized_output_path(
        self,
        perturbation_json_path: Path,
        method_name: str,
        run_timestamp: str
    ) -> Path:
        """
        Get organized output path: output_attacked_pdfs/timestamp/subject/level/question_paper_name/
        
        Args:
            perturbation_json_path: Path to perturbation JSON file
            method_name: Injection method name
            run_timestamp: Timestamp for this run
            
        Returns:
            Path to output directory
        """
        metadata = extract_metadata_from_json(perturbation_json_path)
        subject = metadata['subject']
        level = metadata['level']
        document_name = metadata['document_name']
        
        # Create organized path: output_attacked_pdfs/timestamp/subject/level/question_paper_name/
        output_dir = self.base_output_dir / run_timestamp / subject / level / document_name / method_name
        
        # Get base filename without _perturbation suffix
        base_name = perturbation_json_path.stem.replace('_perturbation', '')
        output_path = output_dir / f"{base_name}_{method_name}"
        
        return output_path
    
    def process_document(
        self,
        perturbation_json_path: Path,
        methods: List[str] = None,
        run_timestamp: str = None,
        compile_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Process a document and save to organized structure.
        
        Args:
            perturbation_json_path: Path to perturbation JSON file
            methods: List of injection methods to apply
            run_timestamp: Timestamp for this run
            compile_pdf: Whether to compile PDFs
            
        Returns:
            Dictionary with results
        """
        if run_timestamp is None:
            tz = get_timezone(self.config)
            run_timestamp = datetime.now(tz).strftime('%Y%m%d_%H%M%S')
        
        # Temporarily override orchestrator's _get_output_path
        original_get_output_path = self.orchestrator._get_output_path
        
        def organized_get_output_path(pert_path: Path, method: str) -> Path:
            return self._get_organized_output_path(pert_path, method, run_timestamp)
        
        self.orchestrator._get_output_path = organized_get_output_path
        
        try:
            # Process document
            # Filter methods based on config
            if methods:
                enabled_methods = [m for m in methods if m in self.config.injection.methods and self.config.injection.methods[m].enabled]
            else:
                enabled_methods = [m for m in self.config.injection.default_methods if m in self.config.injection.methods and self.config.injection.methods[m].enabled]
            
            if not enabled_methods:
                logger.warning(f"No enabled injection methods found. Skipping {perturbation_json_path.name}")
                return {"error": "No enabled injection methods"}
            
            results = self.orchestrator.process_document(
                perturbation_json_path=perturbation_json_path,
                methods=enabled_methods,
                compile_pdf=compile_pdf and self.config.pdf_generation.compile_pdf
            )
            
            # Add metadata about output location
            metadata = extract_metadata_from_json(perturbation_json_path)
            results['output_metadata'] = {
                'timestamp': run_timestamp,
                'subject': metadata['subject'],
                'level': metadata['level'],
                'document_name': metadata['document_name'],
                'base_output_dir': str(self.base_output_dir)
            }
            
            return results
        finally:
            # Restore original method
            self.orchestrator._get_output_path = original_get_output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate attacked PDFs from perturbation JSON files with organized folder structure"
    )
    parser.add_argument(
        "--perturbation-folder",
        type=str,
        required=True,
        help="Path to folder containing perturbation JSON files (will search recursively)"
    )
    parser.add_argument(
        "--methods",
        type=str,
        nargs="+",
        default=None,
        choices=["icw", "dual_layer", "font_attack", "icw_dual_layer", "icw_font_attack"],
        help="Injection methods to apply (default: all methods)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of documents to process (for testing)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output_attacked_pdfs",
        help="Base output directory (default: output_attacked_pdfs)"
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip PDF compilation (only generate LaTeX)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load config
        config = Config(config_path=args.config)
        
        # Initialize logging with config
        global log_file
        log_file = setup_logging(config)
        if log_file:
            logger.info(f"Logging initialized. Log file: {log_file}")
        
        # Convert to Path
        perturbation_folder = Path(args.perturbation_folder).resolve()
        output_dir = Path(args.output_dir) if args.output_dir else Path(config.pdf_generation.output_base_dir)
        
        # Find perturbation files
        logger.info(f"Searching for perturbation JSON files in: {perturbation_folder}")
        perturbation_files = find_perturbation_files(perturbation_folder)
        
        if not perturbation_files:
            logger.error(f"No perturbation JSON files found in {perturbation_folder}")
            sys.exit(1)
        
        # Apply limit if specified
        if args.limit:
            perturbation_files = perturbation_files[:args.limit]
        
        logger.info(f"Found {len(perturbation_files)} perturbation file(s) to process")
        
        # Create timestamp for this run
        tz = get_timezone(config)
        run_timestamp = datetime.now(tz).strftime('%Y%m%d_%H%M%S')
        logger.info(f"Run timestamp: {run_timestamp}")
        logger.info(f"Output structure: {output_dir}/<timestamp>/<subject>/<level>/<document_name>/<method>/")
        
        # Initialize generator
        generator = OrganizedPDFGenerator(config=config, base_output_dir=output_dir)
        
        # Determine methods
        methods = args.methods if args.methods else None
        if methods is None:
            methods = config.injection.default_methods
        
        logger.info(f"Processing {len(perturbation_files)} document(s) with {len(methods)} method(s)")
        logger.info(f"Methods: {', '.join(methods)}")
        
        # Process each document
        all_results = {}
        total_start = datetime.now(tz)
        
        for i, json_file in enumerate(perturbation_files, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing Document {i}/{len(perturbation_files)}: {json_file.name}")
            logger.info(f"{'='*80}")
            
            doc_start = datetime.now(tz)
            
            # Add delay between documents if configured
            if i > 1 and config.performance.delay_between_documents > 0:
                time.sleep(config.performance.delay_between_documents)
            
            try:
                results = generator.process_document(
                    perturbation_json_path=json_file,
                    methods=methods,
                    run_timestamp=run_timestamp,
                    compile_pdf=not args.no_pdf
                )
                
                all_results[json_file.name] = results
                
                doc_time = (datetime.now(tz) - doc_start).total_seconds()
                
                # Log summary
                logger.info(f"Document processing completed in {doc_time:.2f} seconds")
                logger.info(f"Document ID: {results.get('docid', 'N/A')}")
                
                for method_name, method_result in results.get('methods', {}).items():
                    status = "✓" if method_result.get('success') else "✗"
                    if method_result.get('success'):
                        logger.info(f"  {status} {method_name}: SUCCESS")
                        if 'pdf_compilation' in method_result:
                            pdf_success = method_result['pdf_compilation'].get('success', False)
                            logger.info(f"      PDF: {'✓ Compiled' if pdf_success else '✗ Failed'}")
                        if 'pdf_path' in method_result:
                            logger.info(f"      PDF path: {method_result['pdf_path']}")
                    else:
                        error_msg = method_result.get('error', 'Unknown error')
                        logger.info(f"  {status} {method_name}: FAILED - {error_msg}")
                
            except Exception as e:
                logger.error(f"ERROR processing {json_file.name}: {e}", exc_info=True)
                all_results[json_file.name] = {"error": str(e)}
        
        # Final summary
        total_time = (datetime.now(tz) - total_start).total_seconds()
        logger.info(f"\n{'='*80}")
        logger.info("Final Summary")
        logger.info(f"{'='*80}")
        
        total_tests = len(perturbation_files) * len(methods)
        successful_tests = 0
        successful_pdfs = 0
        
        for doc_name, doc_results in all_results.items():
            if 'error' in doc_results:
                continue
            
            for method_name, method_result in doc_results.get('methods', {}).items():
                if method_result.get('success'):
                    successful_tests += 1
                    if method_result.get('pdf_compilation', {}).get('success'):
                        successful_pdfs += 1
        
        logger.info(f"Total documents processed: {len(perturbation_files)}")
        logger.info(f"Total methods applied: {total_tests}")
        logger.info(f"Successful injections: {successful_tests}/{total_tests}")
        logger.info(f"Successful PDF compilations: {successful_pdfs}/{total_tests}")
        logger.info(f"Total processing time: {total_time:.2f} seconds")
        logger.info(f"Output directory: {output_dir}/{run_timestamp}/")
        
        # Save results
        results_file = output_dir / run_timestamp / "generation_results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Detailed results saved to: {results_file}")
        
        if successful_tests == total_tests:
            logger.info("\n✓ ALL TESTS PASSED!")
            return 0
        else:
            logger.warning(f"\n⚠ {total_tests - successful_tests} tests failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
