import logging
from logging.handlers import RotatingFileHandler

from .config import settings


def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",
    )
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler (optional)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


