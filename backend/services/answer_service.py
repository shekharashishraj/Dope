"""
Service for saving exam answer submissions.
Handles directory creation and file persistence.
"""

import json
import os
from pathlib import Path
from typing import Dict, Tuple, Optional
from backend.models import SubmitExamRequest
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def sanitize_path_component(component: str) -> str:
    """
    Sanitize a path component to prevent directory traversal.
    
    Args:
        component: Path component to sanitize
        
    Returns:
        Sanitized path component
    """
    # Remove any path separators and dangerous characters
    sanitized = component.replace('/', '').replace('\\', '').replace('..', '')
    # Remove any other potentially dangerous characters
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c in ['-', '_', ' '])
    return sanitized.strip()


def save_answer_submission(payload: SubmitExamRequest, base_dir: str = "Answers") -> Tuple[bool, str, Optional[str]]:
    """
    Save exam answer submission to disk.
    
    Args:
        payload: Validated submission payload
        base_dir: Base directory for storing answers (relative to backend directory)
        
    Returns:
        Tuple of (success: bool, message: str, error_code: Optional[str])
        error_code can be: 'duplicate_attempt', 'invalid_subject', 'filesystem_error'
    """
    try:
        # Get backend directory
        backend_dir = Path(__file__).parent.parent
        answers_base = backend_dir / base_dir
        
        logger.info(f"Saving submission for attempt_id: {payload.attempt.attempt_id}")
        logger.info(f"Subject: {payload.attempt.subject}")
        logger.info(f"Base directory: {answers_base}")
        
        # Sanitize subject name
        subject = sanitize_path_component(payload.attempt.subject)
        if not subject:
            error_msg = "Invalid or empty subject name"
            logger.error(error_msg)
            return False, error_msg, 'invalid_subject'
        
        # Sanitize attempt_id
        attempt_id = sanitize_path_component(payload.attempt.attempt_id)
        if not attempt_id:
            error_msg = "Invalid or empty attempt_id"
            logger.error(error_msg)
            return False, error_msg, 'invalid_attempt_id'
        
        # Build directory path
        attempt_dir = answers_base / subject / attempt_id
        
        logger.info(f"Target directory: {attempt_dir}")
        
        # Check if attempt already exists
        if attempt_dir.exists() and (attempt_dir / "answers.json").exists():
            error_msg = f"Attempt {attempt_id} already exists"
            logger.warning(error_msg)
            return False, error_msg, 'duplicate_attempt'
        
        # Create directory structure (recursive)
        logger.info(f"Creating directory: {attempt_dir}")
        attempt_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory created successfully")
        
        # Convert payload to dict for JSON serialization
        payload_dict = payload.model_dump()
        
        # Write JSON file
        answers_file = attempt_dir / "answers.json"
        logger.info(f"Writing answers to: {answers_file}")
        
        with open(answers_file, 'w', encoding='utf-8') as f:
            json.dump(payload_dict, f, indent=2, ensure_ascii=False)
        
        file_size = answers_file.stat().st_size
        logger.info(f"Answers file written successfully ({file_size} bytes)")
        
        success_msg = f"Submission saved successfully to {answers_file}"
        logger.info(success_msg)
        
        return True, success_msg, None
        
    except OSError as e:
        error_msg = f"Filesystem error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg, 'filesystem_error'
    except Exception as e:
        error_msg = f"Unexpected error saving submission: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg, 'filesystem_error'

