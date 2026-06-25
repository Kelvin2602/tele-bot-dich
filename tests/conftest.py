"""Pytest fixtures chung cho toàn bộ test suite.

Lưu ý: tạo .env.test hoặc override env var trước khi import Settings.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Đảm bảo `src/` nằm trong sys.path
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Set env vars stub TRƯỚC khi import settings (để pydantic-settings đọc được)
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("DEFAULT_TARGET_LANG", "vi")
os.environ.setdefault("LOG_LEVEL", "WARNING")


