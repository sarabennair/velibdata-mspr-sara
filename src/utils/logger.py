"""Logging structure pour VelibData.

Usage:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("ingestion_started", source="velib", records=1400)
"""

import structlog


def get_logger(name: str):
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    return structlog.get_logger(name)
