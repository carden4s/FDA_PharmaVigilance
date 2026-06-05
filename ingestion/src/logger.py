"""Logging configuration for FDA ingestion"""

import logging
import os
import sys
from config import Config

config = Config()


def setup_logger(name: str = "ingestion") -> logging.Logger:
    """Configure structured logging."""

    # Create logs directory if not exists
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # Avoid duplicate handlers when imported multiple times
    if logger.handlers:
        return logger

    # File handler (UTF-8 so ✓ ─ ═ never crash)
    file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL))

    # Console handler — force UTF-8 on the underlying stream (Python 3.7+)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    try:
        console_handler.stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass  # older stream types; safe to ignore

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()