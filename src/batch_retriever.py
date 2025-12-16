"""Script to retrieve and process OpenAI Batch API results."""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import pytz
from logging.handlers import RotatingFileHandler
from .config import Config
from .openai_client import OpenAIClient
from .file_handler import FileHandler

def get_timezone(config):
    """Get timezone from config."""
    timezone_str = config.logging_timezone if config else "America/Denver"
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
    log_file = log_dir / f"batch_retrieval_{timestamp}.log"
    
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


def check_batch_status(batch_id: str, config: Config):
    """Check the status of a batch."""
    client = OpenAIClient(config)
    
    try:
        status = client.check_batch_status(batch_id)
        print(f"\nBatch Status for {batch_id}:")
        print(f"  Status: {status['status']}")
        if status.get('request_counts'):
            counts = status['request_counts']
            print(f"  Total requests: {counts.get('total', 'N/A')}")
            print(f"  Completed: {counts.get('completed', 'N/A')}")
            print(f"  Failed: {counts.get('failed', 'N/A')}")
        
        if status.get('output_file_id'):
            print(f"  Output file ID: {status['output_file_id']}")
        if status.get('error_file_id'):
            print(f"  Error file ID: {status['error_file_id']}")
        
        return status
    except Exception as e:
        logger.error(f"Failed to check batch status: {e}")
        raise


def retrieve_batch_results(batch_id: str, config: Config, output_dir: Optional[Path] = None):
    """Retrieve and process batch results."""
    tz = get_timezone(config)
    retrieval_start = datetime.now(tz)
    logger.info(f"=== Batch retrieval started for batch ID: {batch_id} ===")
    logger.info(f"Start time ({tz.zone}): {retrieval_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    client = OpenAIClient(config)
    
    try:
        # Check status first
        status_start = datetime.now(tz)
        status = check_batch_status(batch_id, config)
        status_time = (datetime.now(tz) - status_start).total_seconds()
        logger.info(f"Status check completed in {status_time:.2f} seconds")
        
        if status['status'] != 'completed':
            logger.warning(f"Batch {batch_id} is not completed yet. Status: {status['status']}")
            logger.info("Available statuses: validating, in_progress, finalizing, completed, expired, cancelled, failed")
            return None
        
        # Determine output directory
        if output_dir is None:
            # Try to find batch info file
            batch_info_file = None
            for possible_dir in Path("output").rglob("batch_info.json"):
                with open(possible_dir, 'r') as f:
                    batch_info = json.load(f)
                    if batch_id in batch_info:
                        batch_info_file = possible_dir
                        batch_data = batch_info[batch_id]
                        output_dir = Path(batch_data['output_dir'])
                        json_file = Path(batch_data['json_file'])
                        break
            
            if output_dir is None:
                # Default output directory
                output_dir = Path("output") / "batch_results" / batch_id
                output_dir.mkdir(parents=True, exist_ok=True)
                logger.warning(f"Could not find batch info file. Using default output: {output_dir}")
        
        # Download results
        download_start = datetime.now(tz)
        results_file = output_dir / f"{batch_id}_results.jsonl"
        logger.info(f"Downloading batch results to: {results_file}")
        client.download_batch_results(batch_id, results_file)
        download_time = (datetime.now(tz) - download_start).total_seconds()
        logger.info(f"Download completed in {download_time:.2f} seconds")
        
        # Parse results
        parse_start = datetime.now(tz)
        logger.info("Parsing batch results...")
        perturbations = client.parse_batch_results(results_file)
        parse_time = (datetime.now(tz) - parse_start).total_seconds()
        logger.info(f"Parsing completed in {parse_time:.2f} seconds")
        
        # Log summary of parsed results
        total_perturbations = sum(len(pert) for pert in perturbations.values())
        logger.info(f"Parsed {total_perturbations} total perturbations across {len(perturbations)} questions")
        
        # Initialize timing variables for summary
        merge_time = 0.0
        save_time = 0.0
        output_path = None
        
        # Load original JSON file if we found batch info
        if batch_info_file:
            with open(batch_info_file, 'r') as f:
                batch_info = json.load(f)
                batch_data = batch_info[batch_id]
                json_file = Path(batch_data['json_file'])
                
                # Load original data
                file_handler = FileHandler()
                data = file_handler.load_json_file(json_file)
                
                # Merge perturbations back into question data
                merge_start = datetime.now(tz)
                questions = data.get('questions', [])
                total_merged = 0
                for question in questions:
                    question_number = question.get('question_number')
                    if question_number in perturbations:
                        pert_count = len(perturbations[question_number])
                        question['perturbations'] = perturbations[question_number]
                        total_merged += pert_count
                        logger.info(f"Question {question_number}: {pert_count} perturbations merged")
                        # Log perturbations details at DEBUG level
                        logger.debug(f"Question {question_number} - Perturbations: {json.dumps(perturbations[question_number], indent=2)}")
                    else:
                        question['perturbations'] = []
                        logger.warning(f"Question {question_number}: No perturbations found in batch results")
                merge_time = (datetime.now(tz) - merge_start).total_seconds()
                logger.info(f"Perturbation merge completed in {merge_time:.2f} seconds")
                logger.info(f"Total perturbations merged: {total_merged} across {len(questions)} questions")
                
                # Save output
                save_start = datetime.now(tz)
                output_path = file_handler.save_perturbed_json(
                    output_dir=Path(batch_data['output_dir']),
                    original_json_path=json_file,
                    perturbed_data=data
                )
                save_time = (datetime.now(tz) - save_start).total_seconds()
                logger.info(f"Saved perturbed JSON to: {output_path} (took {save_time:.2f} seconds)")
                
                # Log detailed summary
                retrieval_time = (datetime.now(tz) - retrieval_start).total_seconds()
                logger.info(f"=== Batch retrieval completed for batch ID: {batch_id} ===")
                logger.info(f"Total retrieval time: {retrieval_time:.2f} seconds")
                logger.info(f"End time ({tz.zone}): {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
                logger.info(f"=== Detailed Summary ===")
                logger.info(f"  Batch ID: {batch_id}")
                logger.info(f"  Status check: {status_time:.2f}s")
                logger.info(f"  Download: {download_time:.2f}s")
                logger.info(f"  Parse: {parse_time:.2f}s")
                logger.info(f"  Merge: {merge_time:.2f}s")
                logger.info(f"  Save: {save_time:.2f}s")
                logger.info(f"  Total: {retrieval_time:.2f}s")
                logger.info(f"  Questions processed: {len(questions)}")
                logger.info(f"  Total perturbations: {total_merged}")
                logger.info(f"  Output path: {output_path}")
                
                # Update batch info
                batch_info[batch_id]['status'] = 'completed'
                batch_info[batch_id]['completed_at'] = __import__('datetime').datetime.now().isoformat()
                batch_info[batch_id]['output_path'] = str(output_path)
                
                with open(batch_info_file, 'w') as f:
                    json.dump(batch_info, f, indent=2)
                
                return output_path
        else:
            # Just save the parsed results
            results_json = output_dir / f"{batch_id}_perturbations.json"
            with open(results_json, 'w') as f:
                json.dump(perturbations, f, indent=2)
            logger.info(f"Saved parsed perturbations to: {results_json}")
            return results_json
        
    except Exception as e:
        logger.error(f"Failed to retrieve batch results: {e}", exc_info=True)
        raise


def list_batches(config: Config):
    """List all batches from batch_info.json files."""
    batch_files = list(Path("output").rglob("batch_info.json"))
    
    if not batch_files:
        print("No batch info files found.")
        return
    
    all_batches = []
    for batch_file in batch_files:
        try:
            with open(batch_file, 'r') as f:
                batch_info = json.load(f)
                for batch_id, data in batch_info.items():
                    data['batch_id'] = batch_id
                    data['batch_info_file'] = str(batch_file)
                    all_batches.append(data)
        except Exception as e:
            logger.warning(f"Failed to read {batch_file}: {e}")
    
    if not all_batches:
        print("No batches found in batch info files.")
        return
    
    print(f"\nFound {len(all_batches)} batch(es):\n")
    for i, batch in enumerate(all_batches, 1):
        print(f"{i}. Batch ID: {batch['batch_id']}")
        print(f"   Status: {batch.get('status', 'unknown')}")
        print(f"   Submitted: {batch.get('submitted_at', 'unknown')}")
        print(f"   JSON File: {batch.get('json_file', 'unknown')}")
        if batch.get('completed_at'):
            print(f"   Completed: {batch['completed_at']}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Retrieve and process OpenAI Batch API results"
    )
    parser.add_argument(
        "--batch-id",
        type=str,
        help="Batch ID to check or retrieve"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for results (default: auto-detect from batch_info.json)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all batches from batch_info.json files"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check status, don't download results"
    )
    
    args = parser.parse_args()
    
    try:
        config = Config(config_path=args.config)
        
        # Initialize logging with config
        global log_file
        log_file = setup_logging(config)
        if log_file:
            logger.info(f"Logging initialized. Log file: {log_file}")
        
        if args.list:
            list_batches(config)
            return
        
        if not args.batch_id:
            parser.error("--batch-id is required (or use --list to see available batches)")
        
        if args.check_only:
            check_batch_status(args.batch_id, config)
        else:
            output_dir = Path(args.output_dir) if args.output_dir else None
            retrieve_batch_results(args.batch_id, config, output_dir)
            
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
