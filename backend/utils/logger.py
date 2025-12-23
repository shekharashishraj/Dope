"""
Logging configuration for the backend application.
Sets up file and console logging with timestamps.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: str = "logs") -> str:
    """
    Setup logging configuration for the backend.
    
    Args:
        log_dir: Directory to store log files (relative to backend/)
        
    Returns:
        Path to the log file created
    """
    # Get the backend directory (parent of utils/)
    backend_dir = Path(__file__).parent.parent
    log_path = backend_dir / log_dir
    
    # Create logs directory if it doesn't exist
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_path / f"backend_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True  # Override any existing configuration
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Logging initialized")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 80)
    
    return str(log_file)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

