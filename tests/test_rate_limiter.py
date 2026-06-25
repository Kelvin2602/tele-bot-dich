"""Test cho rate limiter service (sliding window per-user)."""

from __future__ import annotations

import time

import pytest

from tele_bot_dich.services.rate_limiter import (
    SlidingWindowRateLimiter,
    RateLimitResult,
    set_rate_limiter,
)


class TestSlidingWindowRateLimiter:
    """Unit tests cho SlidingWindowRateLimiter."""

    def test_init_defaults(self) -> None:
        limiter = SlidingWindowRateLimiter()
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60

    def test_init_custom_values(self) -> None:
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=30)
        assert limiter.max_requests == 5
        assert limiter.window_seconds == 30

    def test_init_invalid_max_requests(self) -> None:
        with pytest.raises(ValueError, match="max_requests"):
            SlidingWindowRateLimiter(max_requests=0)

    def test_init_invalid_window_seconds(self) -> None:
        with pytest.raises(ValueError, match="window_seconds"):
            SlidingWindowRateLimiter(window_seconds=0)

    def test_first_request_allowed(self) -> None:
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        result = limiter.check(user_id=1)
        assert result.allowed is True
        assert result.remaining == 2
        assert result.reset_after == 0.0

    def test_requests_within_limit(self) -> None:
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)

        # 3 requests liên tiếp — tất cả đều allowed
        for i in range(3):
            result = limiter.check(user_id=2)
            assert result.allowed is True, f"Request {i+1} should be allowed"
            assert result.remaining == 2 - i

    def test_exceeds_limit(self) -> None:
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)

        limiter.check(user_id=3)  # 1/2
        limiter.check(user_id=3)  # 2/2

        # Vượt quá giới hạn
        result = limiter.check(user_id=3)
        assert result.allowed is False
        assert result.remaining == 0
        assert result.reset_after > 0

    def test_window_expires(self) -> None:
        """Sau khi window hết hạn, request mới được phép."""
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=1)

        # Request đầu — allowed
        result = limiter.check(user_id=4)
        assert result.allowed is True

        # Request thứ 2 ngay lập tức — denied
        result = limiter.check(user_id=4)
        assert result.allowed is False

        # Chờ 1s cho window hết hạn
        time.sleep(1.1)

        # Request mới — allowed (window đã reset)
        result = limiter.check(user_id=4)
        assert result.allowed is True

    def test_different_users_independent(self) -> None:
        """Rate limit hoạt động độc lập cho mỗi user."""
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)

        # User A: 1/1
        assert limiter.check(user_id=10).allowed is True
        # User A: denied
        assert limiter.check(user_id=10).allowed is False

        # User B: vẫn allowed (user khác)
        assert limiter.check(user_id=11).allowed is True
        # User B: denied
        assert limiter.check(user_id=11).allowed is False

        # User C: allowed
        assert limiter.check(user_id=12).allowed is True

    def test_reset_user(self) -> None:
        """reset() xoá dữ liệu rate limit của 1 user."""
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)

        limiter.check(user_id=20)  # 1/1
        assert limiter.check(user_id=20).allowed is False  # denied

        limiter.reset(user_id=20)

        # Sau reset, lại được phép
        result = limiter.check(user_id=20)
        assert result.allowed is True

    def test_get_remaining(self) -> None:
        """get_remaining() trả về số request còn lại."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)

        # Chưa có request nào
        assert limiter.get_remaining(user_id=30) == 5

        limiter.check(user_id=30)  # 1/5
        assert limiter.get_remaining(user_id=30) == 4

        limiter.check(user_id=30)  # 2/5
        assert limiter.get_remaining(user_id=30) == 3

    def test_remaining_goes_to_zero(self) -> None:
        """Khi hết quota, remaining = 0."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)

        for _ in range(2):
            limiter.check(user_id=40)

        assert limiter.get_remaining(user_id=40) == 0
        result = limiter.check(user_id=40)
        assert result.remaining == 0

    def test_result_dataclass_types(self) -> None:
        """RateLimitResult có đúng types."""
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)

        allowed = limiter.check(user_id=50)
        assert isinstance(allowed, RateLimitResult)
        assert isinstance(allowed.allowed, bool)
        assert isinstance(allowed.remaining, int)
        assert isinstance(allowed.reset_after, float)

        limiter.check(user_id=50)
        limiter.check(user_id=50)
        denied = limiter.check(user_id=50)
        assert isinstance(denied, RateLimitResult)
        assert denied.allowed is False
        assert denied.remaining == 0
        assert denied.reset_after > 0


# === Test integration: rate limiter + handle_text ===


@pytest.mark.asyncio
async def test_handle_text_rate_limited() -> None:
    """Khi user vượt rate limit, handler trả về thông báo và không gọi translator."""
    from unittest.mock import AsyncMock, MagicMock

    from tele_bot_dich.handlers import translate as translate_handler

    user_id = 4001

    # Tạo rate limiter với max=1
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
    set_rate_limiter(limiter)

    # Mock translator
    mock_translator = MagicMock()
    mock_result = MagicMock()
    mock_result.source_lang = "en"
    mock_result.target_lang = "vi"
    mock_result.translated = "Xin chào"
    mock_translator.translate = AsyncMock(return_value=mock_result)
    translate_handler.set_translator(mock_translator)

    # Request 1: allowed
    update1 = MagicMock()
    update1.effective_user = MagicMock()
    update1.effective_user.id = user_id
    update1.effective_user.username = "tester"
    update1.effective_chat = MagicMock()
    update1.effective_chat.id = user_id
    update1.message = MagicMock()
    update1.message.text = "Hello world"
    update1.message.reply_text = AsyncMock()
    context1 = MagicMock()
    context1.bot = MagicMock()
    context1.bot.send_chat_action = AsyncMock()
    context1.args = []

    await translate_handler.handle_text(update1, context1)

    # Translator được gọi (rate limit OK)
    assert mock_translator.translate.await_count == 1

    # Request 2: rate limited
    update2 = MagicMock()
    update2.effective_user = MagicMock()
    update2.effective_user.id = user_id
    update2.effective_user.username = "tester"
    update2.effective_chat = MagicMock()
    update2.effective_chat.id = user_id
    update2.message = MagicMock()
    update2.message.text = "Hello again"
    update2.message.reply_text = AsyncMock()
    context2 = MagicMock()
    context2.bot = MagicMock()
    context2.bot.send_chat_action = AsyncMock()
    context2.args = []

    await translate_handler.handle_text(update2, context2)

    # Translator KHÔNG được gọi thêm (rate limit denied)
    assert mock_translator.translate.await_count == 1

    # User nhận được message rate limit
    update2.message.reply_text.assert_called_once()
    text = update2.message.reply_text.call_args.args[0]
    assert "quá nhiều" in text or "đợi" in text

    # Cleanup
    translate_handler.set_translator(None)
    set_rate_limiter(None)
