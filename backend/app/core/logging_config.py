"""
Structured logging setup using loguru.
Enterprise apps need traceable, timestamped, leveled logs, not print statements.
"""
import sys
from loguru import logger


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )
    logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="DEBUG")


__all__ = ["logger", "configure_logging"]
