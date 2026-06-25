"""In-memory store cho setting của từng user (theo user_id).

Mở rộng tương lai: thay bằng SQLite/Redis khi cần persist qua restart.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from tele_bot_dich.config import settings


@dataclass(slots=True)
class UserSettings:
    """Settings của 1 user."""

    target_lang: str = settings.default_target_lang


class UserSettingsStore:
    """Thread-safe in-memory store: user_id → UserSettings."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._data: dict[int, UserSettings] = {}

    def get(self, user_id: int) -> UserSettings:
        """Lấy setting; nếu chưa có thì tạo mới với default."""
        with self._lock:
            cfg = self._data.get(user_id)
            if cfg is None:
                cfg = UserSettings()
                self._data[user_id] = cfg
            return cfg

    def get_target(self, user_id: int) -> str:
        return self.get(user_id).target_lang

    def set_target(self, user_id: int, target_lang: str) -> None:
        with self._lock:
            self._data[user_id] = UserSettings(target_lang=target_lang.lower())


# Singleton toàn cục
user_settings_store = UserSettingsStore()

__all__ = ["UserSettings", "UserSettingsStore", "user_settings_store"]
