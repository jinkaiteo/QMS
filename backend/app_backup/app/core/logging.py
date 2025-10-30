"""
Simple Logging Configuration for QMS Platform v3.0
Replacement for complex logging.py with minimal dependencies
"""

import logging
import sys
from pathlib import Path


def configure_logging(log_level: str = "INFO"):
    """Configure simple logging for the QMS application"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "qms.log")
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("QMS Platform logging configured successfully")
    
    return logger


def get_logger(name: str):
    """Get a logger instance"""
    return logging.getLogger(name)