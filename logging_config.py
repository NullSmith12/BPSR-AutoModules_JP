"""
Logging configuration
"""

import logging
import os
from datetime import datetime


def setup_logging(level=logging.INFO, debug_mode=False):
    """
    Logging configuration
    
    Args:
        level: Logging level
        debug_mode: Whether in debug mode
    """
    # If already configured, return directly
    if logging.getLogger().handlers:
        return
    
    # Set logging level
    if debug_mode:
        level = logging.DEBUG
    
    # Create log directory in user's home directory
    log_dir = os.path.join(os.path.expanduser('~'), '.star_resonance_logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log file name (including timestamp)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"star_resonance_{timestamp}.log")
    
    # Configure log format
    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Log configuration information
    logger = logging.getLogger(__name__)
    logger.info(f"Logging system initialized - Level: {logging.getLevelName(level)}")
    logger.info(f"Log file: {log_file}")


def get_logger(name):
    """
    Gets a logger with the specified name
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
