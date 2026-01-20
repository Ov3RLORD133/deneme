"""
Structured logging configuration for KeyChaser.

Provides dual output (console + file) with color-coded console logs
and detailed file logs including malware traffic analysis metadata.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with ANSI color codes for console output.
    
    Security events (malware connections, decryption) are highlighted
    for quick visual identification during analysis.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Apply color formatting to log level."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure a logger with console and optional file handlers.
    
    Args:
        name: Logger name (typically module name)
        log_file: Optional specific log file name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if settings.log_to_file:
        if log_file is None:
            log_file = f"keychaser_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_path = settings.log_path / log_file
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for the specified module.
    
    Args:
        name: Logger name (use __name__ in calling module)
        
    Returns:
        Configured logger instance
    """
    return setup_logger(name)


# Create a dedicated logger for traffic analysis
def get_traffic_logger() -> logging.Logger:
    """
    Get specialized logger for malware traffic analysis.
    
    Logs are written to a separate file for forensic review.
    """
    return setup_logger("keychaser.traffic", "traffic.log")
