"""PyTVPaint package logger."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _get_logger() -> logging.Logger:
    log_format = "[%(asctime)s] %(name)s / %(levelname)s -- %(message)s"
    formatter = logging.Formatter(log_format)

    logger_name = "pytvpaint"
    logger = logging.getLogger(logger_name)
    log_level = logging.getLevelName(os.getenv("PYTVPAINT_LOG_LEVEL", "INFO").upper())

    logger.setLevel(log_level)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    log_path = os.getenv("PYTVPAINT_LOG_PATH", "")
    if log_path:
        log_path_obj = Path(log_path)
        log_path_obj.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_path_obj.as_posix(),
            mode="a+",
            maxBytes=1024 * 1024,
            backupCount=5,
        )

        file_handler.set_name(logger_name)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    return logger


log = _get_logger()
