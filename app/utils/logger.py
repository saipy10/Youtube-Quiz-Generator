import logging
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "youtube_quiz.log"

_is_configured = False


def setup_logger(name: str = "youtube_quiz") -> logging.Logger:
    """Configures and returns a logger instance with console and file handlers."""
    global _is_configured
    logger = logging.getLogger(name)

    if not _is_configured:
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        _is_configured = True

    return logger


def mask_secret(secret: str | None, visible_chars: int = 4) -> str:
    """Safely masks a secret string to avoid logging sensitive data."""
    if not secret:
        return "[NOT SET]"
    if len(secret) <= visible_chars:
        return "****"
    return f"{secret[:visible_chars]}...****"
