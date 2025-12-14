"""Main processing pipeline for generating perturbations."""
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from .config import Config
from .file_handler import FileHandler
from .openai_client import OpenAIClient
from prompts.mcq_prompt import format_mcq_prompt
from prompts.tf_prompt import format_tf_prompt
from prompts.long_prompt import format_long_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    
    def process_all_files(self, limit: Optional[int] = None, force: bool = False):
        """
        Process JSON files in the input directory.
        
        Args:
            limit: Optional limit on number of files to process (for testing)
            force: If True, reprocess files even if they already exist (overrides resume setting)
        """
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
            
            for json_file, latex_file, output_dir in batch:
                try:
                    # Check if already processed (skip if resume is enabled and not forcing)
                    if not force and self.config.resume and self.file_handler.is_already_processed(output_dir, json_file):
                        logger.info(f"Skipping already processed file: {json_file.name}")
                        total_skipped += 1
                        continue
                    
                    # Process single document
                    self.process_document(json_file, latex_file, output_dir)
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
        output_dir: Path
    ):
        """
        Process a single document.
        
        Args:
            json_file: Path to JSON file
            latex_file: Path to LaTeX file (can be None)
            output_dir: Output directory path
        """
        # Load JSON data
        data = self.file_handler.load_json_file(json_file)
        
        # Extract questions
        questions = data.get('questions', [])
        if not questions:
            logger.warning(f"No questions found in {json_file.name}")
            return
        
        # Prepare questions for processing
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
                
                question_prompts[question_number] = prompt
                question_metadata[question_number] = question
                
            except Exception as e:
                logger.error(f"Error formatting prompt for question {question_number}: {e}")
                continue
        
        # Generate perturbations
        logger.info(f"Generating perturbations for {len(question_prompts)} questions in {json_file.name}")
        perturbations = self.openai_client.batch_generate_perturbations(question_prompts)
        
        # Merge perturbations back into question data
        for question in questions:
            question_number = question.get('question_number')
            if question_number in perturbations:
                question['perturbations'] = perturbations[question_number]
            else:
                question['perturbations'] = []
        
        # Save output
        output_path = self.file_handler.save_perturbed_json(
            output_dir=output_dir,
            original_json_path=json_file,
            perturbed_data=data
        )
        
        logger.info(f"Saved perturbed JSON to: {output_path}")


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
    
    args = parser.parse_args()
    
    # --no-resume is an alias for --force
    force = args.force or args.no_resume
    
    try:
        config = Config(config_path=args.config)
        processor = Processor(config)
        processor.process_all_files(limit=args.limit, force=force)
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

