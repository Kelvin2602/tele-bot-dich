"""Cấu hình loguru dùng chung cho toàn bộ ứng dụng."""

from __future__ import annotations

import sys

from loguru import logger

from tele_bot_dich.config import settings


def setup_logger() -> None:
    """Khởi tạo loguru handler mặc định. Gọi 1 lần khi start app."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )


__all__ = ["logger", "setup_logger"]
