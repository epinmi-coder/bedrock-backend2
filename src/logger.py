
import logging
import sys
import os
import io
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

# Configure UTF-8 encoding for stdout/stderr on Windows BEFORE any logging setup
if sys.platform == 'win32':
    # Reconfigure stdout and stderr to use UTF-8 encoding
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Get log level from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "app.log"))
ERROR_LOG_FILE = str(LOGS_DIR / "error.log")
ACCESS_LOG_FILE = str(LOGS_DIR / "access.log")


# Custom formatter with colors for console
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
  
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
        
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
        
    
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with colors (sys.stdout already configured for UTF-8 on Windows)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler for all logs (with UTF-8 encoding)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler for errors only (with UTF-8 encoding)
    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


def log_request(request, response_status: int, processing_time: float):
    
    access_logger = logging.getLogger("access")
    
    if not access_logger.handlers:
        # Set up access logger (with UTF-8 encoding)
        access_handler = logging.FileHandler(ACCESS_LOG_FILE, encoding='utf-8')
        access_formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        access_handler.setFormatter(access_formatter)
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
    
    # Log request details
    access_logger.info(
        f"{request.client.host} - {request.method} {request.url.path} "
        f"- {response_status} - {processing_time:.3f}s"
    )


# Create default logger
logger = setup_logger(__name__, LOG_LEVEL)

# Export commonly used functions
__all__ = ["setup_logger", "log_request", "logger"]

# Export common logger for backward compatibility
logging.getLogger().setLevel(logging.INFO)

