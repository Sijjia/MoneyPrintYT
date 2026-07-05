"""
core/logger.py
Централизованное логирование через rich для красивого CLI.
"""
import logging
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def setup_logger(name: str = "webik", level: int = logging.INFO, log_file: Path = None) -> logging.Logger:
    """Создаёт логгер с rich-форматом + опциональным файлом."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # Console handler через rich
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        show_time=True,
        show_path=False,
        markup=True,
    )
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(rich_handler)

    # File handler если указан
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    return logger


# Глобальный логгер по умолчанию
log = setup_logger()
