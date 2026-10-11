"""Logging.

One consistently formatted logger for scripts and the engine.
"""

from __future__ import annotations

import logging


def get_logger(name: str = "creditengine", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
