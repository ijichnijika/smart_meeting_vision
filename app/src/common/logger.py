"""
日志配置与获取模块。
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str = "meeting_vision") -> logging.Logger:
    """获取控制台 + 文件输出的格式化日志器。"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        level_name = os.environ.get("MEETING_VISION_LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, level_name, logging.INFO))

        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        try:
            log_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_dir / "meeting_vision.log",
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    return logger
