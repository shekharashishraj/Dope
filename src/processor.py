"""Main processing pipeline for generating perturbations."""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import pytz
from logging.handlers import RotatingFileHandler
from .config import Config
from .file_handler import FileHandler
from .openai_client import OpenAIClient
from prompts.mcq_prompt import format_mcq_prompt
from prompts.tf_prompt import format_tf_prompt
from prompts.long_prompt import format_long_prompt

# Global config will be set after Config is imported
_config = None
MST = None

def get_timezone(config):
    """Get timezone from config."""
    global MST
    if MST is None:
        timezone_str = config.logging_timezone if config else "America/Denver"
        MST = pytz.timezone(timezone_str)
    return MST

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
    if not config or not config.logging_enabled:
        # Basic logging if disabled or no config
        logging.basicConfig(level=logging.INFO)
        return None
    
    if log_dir is None:
        log_dir = Path(config.logging_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get timezone
    tz = get_timezone(config)
    
    # Create log filename with timestamp
    timestamp = datetime.now(tz).strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"perturbation_{timestamp}.log"
    
    # Create formatter with configured timezone
    formatter = MSTFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z',
        config=config
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.logging_max_bytes,
        backupCount=config.logging_backup_count
    )
    file_level = getattr(logging, config.logging_file_level.upper(), logging.DEBUG)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_level = getattr(logging, config.logging_console_level.upper(), logging.INFO)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_level = getattr(logging, config.logging_level.upper(), logging.INFO)
    root_logger.setLevel(root_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return log_file

# Initialize logging will be done after Config is loaded
log_file = None
logger = logging.getLogger(__name__)


class Processor:
    """Main processor for the perturbation pipeline."""
    
    def __init__(self, config: Config):
        """
        Initialize processor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.file_handler = FileHandler(
            input_dir=config.input_dir,
            output_suffix=config.output_suffix
        )
        self.openai_client = OpenAIClient(config)
        self.mappings_per_question = config.mappings_per_question
    
    def process_all_files(self, limit: Optional[int] = None, force: bool = False, mode: str = "immediate"):
        """
        Process JSON files in the input directory.
        
        Args:
            limit: Optional limit on number of files to process (for testing)
            force: If True, reprocess files even if they already exist (overrides resume setting)
            mode: Processing mode - "immediate" or "batch"
        """
        # Create timestamp for the run (shared across all documents)
        # Both batch and immediate modes use organized structure with shared timestamp
        tz = get_timezone(self.config)
        run_timestamp = datetime.now(tz).strftime('%Y%m%d_%H%M%S')
        if mode == "batch":
            logger.info(f"Batch run timestamp: {run_timestamp} (shared across all documents)")
        else:
            logger.info(f"Immediate run timestamp: {run_timestamp} (shared across all documents)")
        
        batch_timestamp = run_timestamp  # Use same variable name for compatibility
        
        # Discover all JSON files
        json_files = self.file_handler.discover_json_files()
        total_files = len(json_files)
        
        # Apply limit if specified
        if limit is not None and limit > 0:
            json_files = json_files[:limit]
            logger.info(f"Found {total_files} JSON files total, processing first {len(json_files)} files (limit={limit})")
        else:
            logger.info(f"Found {len(json_files)} JSON files to process")
        
        # Group files into batches
        batch_size = self.config.batch_size
        batches = [
            json_files[i:i + batch_size] 
            for i in range(0, len(json_files), batch_size)
        ]
        
        logger.info(f"Processing {len(batches)} batches of up to {batch_size} documents each")
        
        total_processed = 0
        total_skipped = 0
        
        for batch_idx, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {batch_idx}/{len(batches)}")
            
            for json_file, latex_file, original_output_dir in batch:
                try:
                    # Both modes now use organized structure, so we check in the organized location
                    # Note: We can't check until we know the organized path, so we'll check inside process_document
                    # Process single document
                    # output_dir will be reorganized in process_document for both modes
                    self.process_document(json_file, latex_file, original_output_dir, mode=mode, batch_timestamp=batch_timestamp, force=force)
                    total_processed += 1
                    logger.info(f"Successfully processed: {json_file.name}")
                    
                except Exception as e:
                    logger.error(f"Error processing {json_file.name}: {e}", exc_info=True)
                    continue
        
        logger.info(f"Processing complete. Processed: {total_processed}, Skipped: {total_skipped}")
    
    def process_document(
        self, 
        json_file: Path, 
        latex_file: Path, 
        output_dir: Path,
        mode: str = "immediate",
        batch_timestamp: Optional[str] = None,
        force: bool = False
    ):
        """
        Process a single document.
        
        Args:
            json_file: Path to JSON file
            latex_file: Path to LaTeX file (can be None)
            output_dir: Output directory path
            mode: Processing mode - "immediate" or "batch"
            batch_timestamp: Timestamp for batch runs (used for organized output structure)
            force: If True, reprocess even if output already exists
        """
        tz = get_timezone(self.config)
        doc_start_time = datetime.now(tz)
        logger.info(f"=== Starting document processing: {json_file.name} ===")
        logger.info(f"Document: {json_file}")
        logger.info(f"Mode: {mode}")
        logger.info(f"Start time ({tz.zone}): {doc_start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Load JSON data
        load_start = datetime.now(tz)
        data = self.file_handler.load_json_file(json_file)
        load_time = (datetime.now(tz) - load_start).total_seconds()
        logger.debug(f"JSON load time: {load_time:.2f} seconds")
        
        # Extract metadata for organized output structure (both batch and immediate modes)
        # Extract subject, level, and question paper name from JSON
        subject = data.get('domain', 'unknown')
        level = data.get('academic_level', 'unknown').lower()
        docid = data.get('docid', json_file.stem)
        question_paper_name = docid  # e.g., "cybersecurity_undergraduate_doc_01"
        
        # Create organized output directory: output_perturbation/timestamp/subject/level/question_paper_name/
        if self.config.use_organized_structure:
            base_output = Path(self.config.output_base_dir)
        else:
            # Fallback to old structure
            base_output = Path("output")
        # batch_timestamp is now set for both modes (shared timestamp for the run)
        organized_output_dir = base_output / batch_timestamp / subject / level / question_paper_name
        output_dir = organized_output_dir
        
        logger.info(f"Organized output structure: {organized_output_dir}")
        logger.info(f"Subject: {subject}, Level: {level}, Question Paper: {question_paper_name}")
        
        # Check if already processed (for resume mode)
        if not force and self.config.resume:
            # Check in the organized output location
            if self.file_handler.is_already_processed(output_dir, json_file):
                logger.info(f"Skipping already processed file: {json_file.name}")
                return
        
        # Extract questions
        questions = data.get('questions', [])
        if not questions:
            logger.warning(f"No questions found in {json_file.name}")
            return
        
        logger.info(f"Found {len(questions)} questions in document")
        
        # Prepare questions for processing
        prompt_prep_start = datetime.now(tz)
        question_prompts = {}
        question_metadata = {}
        
        for question in questions:
            question_number = question.get('question_number')
            question_type = question.get('question_type', '').upper()
            
            if not question_number:
                logger.warning(f"Question missing number in {json_file.name}")
                continue
            
            # Get LaTeX stem text
            latex_stem_text = self.file_handler.get_latex_stem_for_question(
                latex_file, 
                question_number
            )
            
            if not latex_stem_text:
                logger.warning(
                    f"Could not find LaTeX stem for question {question_number} in {json_file.name}. "
                    f"Using stem_text as fallback."
                )
                # Fallback to stem_text from JSON
                latex_stem_text = question.get('stem_text', '')
            
            # Get copyable text (plain text version)
            copyable_text = question.get('stem_text', '')
            
            # Get other question data
            gold_answer = question.get('gold_answer', '')
            options = question.get('options', {})
            
            # Format prompt based on question type
            prompt_start = datetime.now(tz)
            try:
                if question_type == 'MCQ':
                    prompt = format_mcq_prompt(
                        latex_stem_text=latex_stem_text,
                        copyable_text=copyable_text,
                        gold_answer=gold_answer,
                        question_type=question_type,
                        options=options,
                        question_index=question_number,
                        k=self.mappings_per_question,
                        reasoning_steps="",  # Empty for now
                        prefix_note="",
                        answer_guidance="",
                        retry_instructions=""
                    )
                elif question_type == 'TF':
                    prompt = format_tf_prompt(
                        latex_stem_text=latex_stem_text,
                        copyable_text=copyable_text,
                        gold_answer=gold_answer,
                        question_type=question_type,
                        question_index=question_number,
                        k=self.mappings_per_question,
                        reasoning_steps="",  # Empty for now
                        prefix_note="",
                        answer_guidance="",
                        retry_instructions=""
                    )
                elif question_type == 'LONG':
                    prompt = format_long_prompt(
                        latex_stem_text=latex_stem_text,
                        copyable_text=copyable_text,
                        gold_answer=gold_answer,
                        question_type=question_type,
                        question_index=question_number,
                        k=self.mappings_per_question,
                        reasoning_steps="",  # Empty for now
                        prefix_note="",
                        answer_guidance="",
                        retry_instructions=""
                    )
                else:
                    logger.warning(f"Unknown question type: {question_type} for question {question_number}")
                    continue
                
                prompt_time = (datetime.now(tz) - prompt_start).total_seconds()
                prompt_length = len(prompt)
                logger.info(f"Question {question_number} ({question_type}): Prompt formatted in {prompt_time:.2f}s, length: {prompt_length} chars")
                logger.info(f"Question {question_number} prompt preview (first 200 chars): {prompt[:200]}...")
                # Log complete prompt at DEBUG level (saved to file)
                logger.debug(f"Question {question_number} ({question_type}) - Complete prompt:\n{prompt}")
                
                question_prompts[question_number] = prompt
                question_metadata[question_number] = question
                
            except Exception as e:
                logger.error(f"Error formatting prompt for question {question_number}: {e}", exc_info=True)
                continue
        
        prompt_prep_time = (datetime.now(tz) - prompt_prep_start).total_seconds()
        logger.info(f"Prompt preparation completed in {prompt_prep_time:.2f} seconds for {len(question_prompts)} questions")
        
        # Generate perturbations based on mode
        if mode == "batch":
            try:
                # Create batch file in the organized output directory
                batch_dir = output_dir / "batch_files"
                batch_dir.mkdir(parents=True, exist_ok=True)
                batch_file = batch_dir / f"{json_file.stem}_batch.jsonl"
                
                logger.info(f"Creating batch file for {len(question_prompts)} questions in {json_file.name}")
                self.openai_client.create_batch_file(question_prompts, batch_file)
                
                # Upload batch file
                logger.info(f"Uploading batch file to OpenAI...")
                batch_id = self.openai_client.upload_batch_file(batch_file)
                
                # Store batch ID for later retrieval (use organized output_dir)
                self._save_batch_info(json_file, batch_id, batch_file, output_dir, data)
                
                logger.info(f"Batch submitted successfully! Batch ID: {batch_id}")
                logger.info(f"Use 'python -m src.batch_retriever --batch-id {batch_id}' to check status and retrieve results")
                
                # Don't save perturbations yet - they'll be retrieved later
                return
                
            except Exception as e:
                logger.error(f"Batch API failed for {json_file.name}: {e}. Falling back to immediate mode.")
                mode = "immediate"
        
        # Initialize timing variables
        api_time = 0.0
        merge_time = 0.0
        save_time = 0.0
        total_perturbations = 0
        output_path = None
        
        # Immediate mode (or fallback from batch mode)
        if mode == "immediate":
            api_start = datetime.now(tz)
            logger.info(f"Generating perturbations for {len(question_prompts)} questions in {json_file.name}")
            logger.info(f"API call start time ({tz.zone}): {api_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            perturbations = self.openai_client.batch_generate_perturbations(question_prompts)
            api_time = (datetime.now(tz) - api_start).total_seconds()
            logger.info(f"API calls completed in {api_time:.2f} seconds")
            
            # Merge perturbations back into question data
            merge_start = datetime.now(tz)
            for question in questions:
                question_number = question.get('question_number')
                if question_number in perturbations:
                    pert_count = len(perturbations[question_number])
                    question['perturbations'] = perturbations[question_number]
                    total_perturbations += pert_count
                    logger.info(f"Question {question_number}: {pert_count} perturbations added")
                    # Log perturbations details at DEBUG level
                    logger.debug(f"Question {question_number} - Perturbations: {json.dumps(perturbations[question_number], indent=2)}")
                else:
                    question['perturbations'] = []
                    logger.warning(f"Question {question_number}: No perturbations generated")
            merge_time = (datetime.now(tz) - merge_start).total_seconds()
            logger.info(f"Perturbation merge time: {merge_time:.2f} seconds")
            logger.info(f"Total perturbations merged: {total_perturbations} across {len(questions)} questions")
            
            # Save output
            # output_dir is already set correctly (organized for batch, original for immediate)
            save_start = datetime.now(tz)
            output_path = self.file_handler.save_perturbed_json(
                output_dir=output_dir,
                original_json_path=json_file,
                perturbed_data=data
            )
            save_time = (datetime.now(tz) - save_start).total_seconds()
            logger.info(f"Saved perturbed JSON to: {output_path} (took {save_time:.2f} seconds)")
        
        doc_total_time = (datetime.now(tz) - doc_start_time).total_seconds()
        doc_end_time = datetime.now(tz)
        
        # Calculate summary statistics
        total_questions = len(questions)
        # Calculate total perturbations if not already set (for batch mode or if immediate mode didn't set it)
        if total_perturbations == 0:
            total_perturbations = sum(len(q.get('perturbations', [])) for q in questions)
        
        logger.info(f"=== Document processing completed: {json_file.name} ===")
        logger.info(f"Total processing time: {doc_total_time:.2f} seconds")
        logger.info(f"Start time ({tz.zone}): {doc_start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"End time ({tz.zone}): {doc_end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Summary - Questions: {total_questions}, Total perturbations: {total_perturbations}")
        if output_path:
            logger.info(f"Output saved to: {output_path}")
        else:
            logger.info(f"Output directory: {output_dir}")
        
        # Log detailed summary at INFO level (so it's saved to file)
        logger.info(f"=== Detailed Summary for {json_file.name} ===")
        logger.info(f"  Document: {json_file}")
        logger.info(f"  Mode: {mode}")
        logger.info(f"  Total questions processed: {total_questions}")
        logger.info(f"  Total perturbations generated: {total_perturbations}")
        logger.info(f"  Processing times:")
        logger.info(f"    - JSON load: {load_time:.2f}s")
        logger.info(f"    - Prompt preparation: {prompt_prep_time:.2f}s")
        if mode == "immediate":
            logger.info(f"    - API calls: {api_time:.2f}s")
            logger.info(f"    - Perturbation merge: {merge_time:.2f}s")
            logger.info(f"    - File save: {save_time:.2f}s")
        logger.info(f"    - Total: {doc_total_time:.2f}s")
        logger.info(f"  Output directory: {output_dir}")
    
    def _save_batch_info(self, json_file: Path, batch_id: str, batch_file: Path, output_dir: Path, data: Dict[str, Any] = None):
        """
        Save batch information for later retrieval.
        
        Args:
            json_file: Original JSON file path
            batch_id: OpenAI batch ID
            batch_file: Path to batch JSONL file
            output_dir: Output directory
            data: JSON data (for extracting metadata)
        """
        batch_info_file = output_dir / "batch_info.json"
        
        # Load existing batch info if it exists
        batch_info = {}
        if batch_info_file.exists():
            try:
                with open(batch_info_file, 'r') as f:
                    batch_info = json.load(f)
            except:
                batch_info = {}
        
        # Extract metadata if data is provided
        metadata = {}
        if data:
            metadata = {
                "subject": data.get('domain', 'unknown'),
                "level": data.get('academic_level', 'unknown'),
                "docid": data.get('docid', 'unknown'),
                "document_name": data.get('document_name', 'unknown')
            }
        
        # Add new batch info
        batch_info[batch_id] = {
            "json_file": str(json_file),
            "batch_file": str(batch_file),
            "output_dir": str(output_dir),
            "submitted_at": datetime.now(get_timezone(self.config)).isoformat(),
            "status": "submitted",
            "metadata": metadata
        }
        
        # Save updated batch info
        with open(batch_info_file, 'w') as f:
            json.dump(batch_info, f, indent=2)
        
        logger.info(f"Saved batch info to: {batch_info_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="IntegrityShield Perturbation Generation Pipeline"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of files to process (for testing). Example: --limit 5"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of all files, even if they already exist (overrides resume setting)"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Disable resume mode - process all files regardless of existing outputs (same as --force)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["immediate", "batch"],
        default="immediate",
        help="Processing mode: 'immediate' for synchronous API calls, 'batch' for OpenAI Batch API (default: immediate)"
    )
    
    args = parser.parse_args()
    
    # --no-resume is an alias for --force
    force = args.force or args.no_resume
    
    try:
        config = Config(config_path=args.config)
        global _config
        _config = config
        
        # Initialize logging with config
        global log_file
        log_file = setup_logging(config)
        if log_file:
            logger.info(f"Logging initialized. Log file: {log_file}")
        
        processor = Processor(config)
        processor.process_all_files(limit=args.limit, force=force, mode=args.mode)
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

