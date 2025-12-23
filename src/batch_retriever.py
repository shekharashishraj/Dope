"""Script to retrieve and process OpenAI Batch API results."""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import pytz
from logging.handlers import RotatingFileHandler
from .config import Config
from .openai_client import OpenAIClient
from .file_handler import FileHandler

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


def _save_logprobs_by_question_type(
    output_dir: Path,
    questions: List[Dict],
    document_name: str
):
    """
    Save logprobs organized by question type in separate folders.
    
    Args:
        output_dir: Output directory for the document
        questions: List of question dictionaries with perturbations
        document_name: Name of the document
    """
    from .models.enums import QuestionType
    
    # Organize logprobs by question type
    logprobs_by_type = {
        "MCQ": [],
        "TF": [],
        "LONG": []
    }
    
    for question in questions:
        question_type = question.get('question_type', '').upper()
        if question_type not in logprobs_by_type:
            continue
        
        for pert in question.get('perturbations', []):
            if pert.get('logprobs'):
                logprob_entry = {
                    "question_number": question.get('question_number'),
                    "question_index": pert.get('question_index'),
                    "original_substring": pert.get('original_substring'),
                    "replacement_substring": pert.get('replacement_substring'),
                    "logprobs": pert.get('logprobs')
                }
                logprobs_by_type[question_type].append(logprob_entry)
    
    # Save logprobs for each question type in separate folders
    for question_type, logprobs_list in logprobs_by_type.items():
        if not logprobs_list:
            continue
        
        # Create folder for this question type
        type_folder = output_dir / "logprobs" / question_type.lower()
        type_folder.mkdir(parents=True, exist_ok=True)
        
        # Save logprobs to JSON file
        logprobs_file = type_folder / f"{document_name}_{question_type.lower()}_logprobs.json"
        with open(logprobs_file, 'w', encoding='utf-8') as f:
            json.dump({
                "document_name": document_name,
                "question_type": question_type,
                "total_perturbations": len(logprobs_list),
                "logprobs": logprobs_list
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(logprobs_list)} logprobs for {question_type} questions to {logprobs_file}")


def _save_research_metrics(
    output_dir: Path,
    questions: List[Dict],
    document_name: str
):
    """
    Compute and save research metrics organized by question type.
    
    Args:
        output_dir: Output directory for the document
        questions: List of question dictionaries with perturbations
        document_name: Name of the document
    """
    import json
    import math
    import numpy as np
    from collections import defaultdict
    
    # Convert dict questions to a format we can work with
    # Organize by question type
    by_type = defaultdict(lambda: {"perturbations": [], "api_metadata": []})
    
    for question in questions:
        question_type = question.get('question_type', '').upper()
        for pert in question.get('perturbations', []):
            by_type[question_type]["perturbations"].append(pert)
            if pert.get('api_metadata'):
                from .models.perturbation import APIMetadata
                try:
                    api_metadata = APIMetadata.model_validate(pert['api_metadata'])
                    by_type[question_type]["api_metadata"].append(api_metadata)
                except:
                    pass
    
    metrics = {
        "by_question_type": {},
        "overall": {}
    }
    
    # Compute metrics for each question type
    for question_type, data in by_type.items():
        perturbations = data["perturbations"]
        api_metadata_list = data["api_metadata"]
        
        type_metrics = {
            "total_perturbations": len(perturbations),
            "logprob_analysis": {},
            "api_metadata_summary": {},
            "cost_analysis": {}
        }
        
        # Compute logprob metrics
        all_entropies = []
        all_confidences = []
        all_token_logprobs = []
        
        for pert in perturbations:
            if pert.get('logprobs'):
                logprobs = pert['logprobs']
                token_logprobs = logprobs.get("token_logprobs", [])
                top_logprobs = logprobs.get("top_logprobs", [])
                
                # Filter out None values
                valid_logprobs = [lp for lp in token_logprobs if lp is not None]
                if valid_logprobs:
                    all_token_logprobs.extend(valid_logprobs)
                    
                    # Compute average confidence (mean logprob)
                    avg_confidence = np.mean(valid_logprobs) if valid_logprobs else None
                    if avg_confidence is not None:
                        all_confidences.append(avg_confidence)
                    
                    # Compute entropy for each token position
                    for top_logprobs_list in top_logprobs:
                        if top_logprobs_list:
                            # Convert logprobs to probabilities
                            probs = [math.exp(lp.get('logprob', -100)) for lp in top_logprobs_list if lp.get('logprob') is not None]
                            if probs:
                                # Normalize probabilities
                                total_prob = sum(probs)
                                if total_prob > 0:
                                    probs = [p / total_prob for p in probs]
                                    # Compute entropy: H = -Σ p(x) * log(p(x))
                                    entropy = -sum(p * math.log(p) if p > 0 else 0 for p in probs)
                                    all_entropies.append(entropy)
        
        # Aggregate logprob metrics
        if all_entropies:
            type_metrics["logprob_analysis"]["avg_entropy"] = float(np.mean(all_entropies))
            type_metrics["logprob_analysis"]["std_entropy"] = float(np.std(all_entropies))
            type_metrics["logprob_analysis"]["min_entropy"] = float(np.min(all_entropies))
            type_metrics["logprob_analysis"]["max_entropy"] = float(np.max(all_entropies))
        
        if all_confidences:
            type_metrics["logprob_analysis"]["avg_confidence"] = float(np.mean(all_confidences))
            type_metrics["logprob_analysis"]["std_confidence"] = float(np.std(all_confidences))
            type_metrics["logprob_analysis"]["min_confidence"] = float(np.min(all_confidences))
            type_metrics["logprob_analysis"]["max_confidence"] = float(np.max(all_confidences))
        
        if all_token_logprobs:
            type_metrics["logprob_analysis"]["total_tokens_with_logprobs"] = len(all_token_logprobs)
        
        # Compute API metadata summary
        if api_metadata_list:
            finish_reasons = [m.finish_reason for m in api_metadata_list if m.finish_reason]
            prompt_tokens = [m.prompt_tokens for m in api_metadata_list if m.prompt_tokens is not None]
            completion_tokens = [m.completion_tokens for m in api_metadata_list if m.completion_tokens is not None]
            total_tokens = [m.total_tokens for m in api_metadata_list if m.total_tokens is not None]
            
            type_metrics["api_metadata_summary"]["total_responses"] = len(api_metadata_list)
            type_metrics["api_metadata_summary"]["finish_reasons"] = {
                reason: finish_reasons.count(reason) for reason in set(finish_reasons)
            }
            type_metrics["api_metadata_summary"]["truncation_rate"] = finish_reasons.count("length") / len(finish_reasons) if finish_reasons else 0
            type_metrics["api_metadata_summary"]["filter_rate"] = finish_reasons.count("content_filter") / len(finish_reasons) if finish_reasons else 0
            
            if prompt_tokens:
                type_metrics["api_metadata_summary"]["avg_prompt_tokens"] = float(np.mean(prompt_tokens))
                type_metrics["api_metadata_summary"]["total_prompt_tokens"] = int(sum(prompt_tokens))
            
            if completion_tokens:
                type_metrics["api_metadata_summary"]["avg_completion_tokens"] = float(np.mean(completion_tokens))
                type_metrics["api_metadata_summary"]["total_completion_tokens"] = int(sum(completion_tokens))
            
            if total_tokens:
                type_metrics["api_metadata_summary"]["avg_total_tokens"] = float(np.mean(total_tokens))
                type_metrics["api_metadata_summary"]["total_tokens"] = int(sum(total_tokens))
            
            # Cost analysis (GPT-4o pricing: $2.50/$10 per 1M tokens)
            if prompt_tokens and completion_tokens:
                total_input_cost = (sum(prompt_tokens) / 1_000_000) * 2.50
                total_output_cost = (sum(completion_tokens) / 1_000_000) * 10.00
                type_metrics["cost_analysis"]["total_cost"] = float(total_input_cost + total_output_cost)
                type_metrics["cost_analysis"]["input_cost"] = float(total_input_cost)
                type_metrics["cost_analysis"]["output_cost"] = float(total_output_cost)
                type_metrics["cost_analysis"]["cost_per_perturbation"] = float((total_input_cost + total_output_cost) / len(perturbations)) if perturbations else 0
        
        metrics["by_question_type"][question_type] = type_metrics
    
    # Compute overall metrics
    all_perturbations = [p for q in questions for p in q.get('perturbations', [])]
    all_api_metadata = [p.get('api_metadata') for q in questions for p in q.get('perturbations', []) if p.get('api_metadata')]
    
    metrics["overall"]["total_perturbations"] = len(all_perturbations)
    metrics["overall"]["total_questions"] = len(questions)
    metrics["overall"]["questions_by_type"] = {
        q.get('question_type', '').upper(): sum(1 for qq in questions if qq.get('question_type', '').upper() == q.get('question_type', '').upper())
        for q in questions
    }
    
    if all_api_metadata:
        from .models.perturbation import APIMetadata
        finish_reasons = []
        for md in all_api_metadata:
            try:
                api_md = APIMetadata.model_validate(md) if isinstance(md, dict) else md
                if api_md.finish_reason:
                    finish_reasons.append(api_md.finish_reason)
            except:
                pass
        metrics["overall"]["truncation_rate"] = finish_reasons.count("length") / len(finish_reasons) if finish_reasons else 0
        metrics["overall"]["filter_rate"] = finish_reasons.count("content_filter") / len(finish_reasons) if finish_reasons else 0
    
    # Save overall metrics
    metrics_file = output_dir / "research_metrics.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump({
            "document_name": document_name,
            "metrics": metrics
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved research metrics to {metrics_file}")
    
    # Also save by question type for easier analysis
    for question_type, type_metrics in metrics["by_question_type"].items():
        type_folder = output_dir / "research_metrics" / question_type.lower()
        type_folder.mkdir(parents=True, exist_ok=True)
        
        type_metrics_file = type_folder / f"{document_name}_{question_type.lower()}_metrics.json"
        with open(type_metrics_file, 'w', encoding='utf-8') as f:
            json.dump({
                "document_name": document_name,
                "question_type": question_type,
                "metrics": type_metrics
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {question_type} research metrics to {type_metrics_file}")


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
                
                # Save logprobs organized by question type
                _save_logprobs_by_question_type(
                    Path(batch_data['output_dir']),
                    questions,
                    json_file.stem
                )
                
                # Save research metrics
                _save_research_metrics(
                    Path(batch_data['output_dir']),
                    questions,
                    json_file.stem
                )
                
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
