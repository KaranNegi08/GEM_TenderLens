"""
GeM TenderLens - Logging Utility
Provides centralized, standardized logger configuration for all application modules.
"""

import io
import logging
import os
import sys

# Ensure UTF-8 IO encoding on Windows to prevent 'charmap' codec errors during emoji logging
os.environ["PYTHONIOENCODING"] = "utf-8"

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

LOG_FILE = "gem_tenderlens.log"
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_global_logger():
    """Initializes global logging config with both file and stream handlers."""
    try:
        stream_handler = logging.StreamHandler(sys.stdout)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        
        handlers = [
            stream_handler,
            file_handler
        ]
        
        logging.basicConfig(
            level=logging.INFO,
            format=LOG_FORMAT,
            datefmt=DATE_FORMAT,
            handlers=handlers
        )
    except Exception as e:
        print(f"Failed to initialize logger: {e}", file=sys.stderr)

# Run initial global setup
setup_global_logger()

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured Logger instance for the specified module name.
    
    Args:
        name (str): Module name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
