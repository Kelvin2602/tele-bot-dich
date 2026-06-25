"""Rate limiter per-user với sliding window.

Dùng sliding window log (lưu timestamp từng request) để quyết định
có cho phép request tiếp theo không. Thread-safe qua `threading.Lock`.

Có thể mở rộng: thay sliding window bằng token bucket hoặc leaky bucket
nếu cần hiệu năng cao hơn cho hàng ngàn user concurrent.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass


@dataclass(slots=True)
class RateLimitResult:
    """Kết quả kiểm tra rate limit cho 1 request.

    Attributes:
        allowed: True nếu request được phép đi tiếp.
        remaining: Số request còn lại trong window hiện tại.
        reset_after: Số giây cho đến khi window reset (0 nếu allowed=True).
    """

    allowed: bool
    remaining: int
    reset_after: float


class SlidingWindowRateLimiter:
    """Rate limiter sliding window per-user.

    Với mỗi user_id, lưu list các timestamp của request trong window
    hiện tại. Khi có request mới:
    1. Xoá các timestamp cũ hơn window_seconds.
    2. Nếu số request trong window < max_requests → allowed.
    3. Nếu đã đạt max → denied, tính reset_after = thời gian đến khi
       request cũ nhất hết hạn.

    Thread-safe: mọi thao tác trên _data đều qua lock.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be >= 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")

        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._lock = threading.Lock()
        # user_id -> list[timestamp] (sorted by insertion order)
        self._data: dict[int, list[float]] = {}

    @property
    def max_requests(self) -> int:
        return self._max_requests

    @property
    def window_seconds(self) -> int:
        return self._window_seconds

    def check(self, user_id: int) -> RateLimitResult:
        """Kiểm tra xem user_id có được phép request không.

        Nếu allowed = True, request được tính vào window (timestamp
        được thêm vào). Handler gọi method này và chỉ proceed nếu
        allowed.

        Args:
            user_id: ID Telegram của user.

        Returns:
            RateLimitResult với trạng thái hiện tại.
        """
        now = time.time()
        cutoff = now - self._window_seconds

        with self._lock:
            timestamps = self._data.get(user_id)
            if timestamps is None:
                # User mới → luôn allowed
                self._data[user_id] = [now]
                return RateLimitResult(
                    allowed=True,
                    remaining=self._max_requests - 1,
                    reset_after=0.0,
                )

            # Xoá timestamp cũ hơn window
            # Duyệt từ đầu list, chỉ giữ lại các timestamp >= cutoff
            # Dùng while để xoá in-place (list thread-safe nhờ lock)
            i = 0
            while i < len(timestamps):
                if timestamps[i] < cutoff:
                    i += 1
                else:
                    break
            if i > 0:
                del timestamps[:i]

            if len(timestamps) >= self._max_requests:
                # Đã đạt giới hạn — tính thời gian chờ
                oldest = timestamps[0]
                reset_after = oldest + self._window_seconds - now
                # Làm tròn lên 0.1s để tránh số âm siêu nhỏ
                if reset_after < 0:
                    reset_after = 0.0
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_after=round(reset_after, 1),
                )

            # Cho phép request
            timestamps.append(now)
            remaining = self._max_requests - len(timestamps)
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_after=0.0,
            )

    def get_remaining(self, user_id: int) -> int:
        """Trả về số request còn lại trong window hiện tại (không thay đổi state)."""
        now = time.time()
        cutoff = now - self._window_seconds

        with self._lock:
            timestamps = self._data.get(user_id)
            if timestamps is None:
                return self._max_requests
            count = sum(1 for ts in timestamps if ts >= cutoff)
            return max(0, self._max_requests - count)

    def reset(self, user_id: int) -> None:
        """Xoá toàn bộ dữ liệu rate limit của 1 user.

        Dùng khi cần reset manual (debug, test, hoặc user được
        nâng hạn mức).
        """
        with self._lock:
            self._data.pop(user_id, None)


# Singleton mặc định
_default_limiter: SlidingWindowRateLimiter | None = None
_limiter_lock = threading.Lock()


def get_rate_limiter(
    max_requests: int | None = None,
    window_seconds: int | None = None,
) -> SlidingWindowRateLimiter:
    """Trả về singleton rate limiter (lazy init từ settings nếu cần)."""
    global _default_limiter
    if _default_limiter is None:
        with _limiter_lock:
            if _default_limiter is None:
                from tele_bot_dich.config import settings as s

                _default_limiter = SlidingWindowRateLimiter(
                    max_requests=max_requests or s.rate_limit_max_requests,
                    window_seconds=window_seconds or s.rate_limit_window_seconds,
                )
    return _default_limiter


def set_rate_limiter(limiter: SlidingWindowRateLimiter) -> None:
    """Inject rate limiter mock (dùng trong test)."""
    global _default_limiter
    _default_limiter = limiter


__all__ = [
    "SlidingWindowRateLimiter",
    "RateLimitResult",
    "get_rate_limiter",
    "set_rate_limiter",
]
