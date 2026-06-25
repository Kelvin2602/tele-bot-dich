"""Test cho handlers: settings (set_target, show_target) và start."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tele_bot_dich.handlers import settings as settings_handlers
from tele_bot_dich.models.user_settings import user_settings_store


def _make_update(user_id: int = 123, text_args: list[str] | None = None) -> MagicMock:
    """Tạo MagicMock giả lập telegram.Update cho command handler."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = user_id
    update.effective_chat = MagicMock()
    update.effective_chat.id = user_id
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


def _make_context(args: list[str] | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.args = args or []
    return ctx


@pytest.mark.asyncio
async def test_set_target_valid() -> None:
    user_id = 1001
    user_settings_store._data.pop(user_id, None)  # reset

    update = _make_update(user_id=user_id)
    context = _make_context(["en"])

    await settings_handlers.set_target(update, context)

    update.message.reply_text.assert_called_once()
    assert user_settings_store.get_target(user_id) == "en"


@pytest.mark.asyncio
async def test_set_target_no_args() -> None:
    update = _make_update(user_id=1002)
    context = _make_context([])

    await settings_handlers.set_target(update, context)

    update.message.reply_text.assert_called_once()
    call_kwargs = update.message.reply_text.call_args.kwargs
    assert "parse_mode" in call_kwargs


@pytest.mark.asyncio
async def test_set_target_invalid_code() -> None:
    update = _make_update(user_id=1003)
    context = _make_context(["eng123"])  # quá dài

    await settings_handlers.set_target(update, context)

    update.message.reply_text.assert_called_once()
    assert "không hợp lệ" in update.message.reply_text.call_args.args[0]


@pytest.mark.asyncio
async def test_show_target() -> None:
    user_id = 1004
    user_settings_store.set_target(user_id, "ja")

    update = _make_update(user_id=user_id)
    context = _make_context([])

    await settings_handlers.show_target(update, context)

    update.message.reply_text.assert_called_once()
    text = update.message.reply_text.call_args.args[0]
    assert "ja" in text


@pytest.mark.asyncio
async def test_quick_set_zh() -> None:
    """`/zh` phải set target sang 'zh' không cần args."""
    user_id = 2001
    user_settings_store._data.pop(user_id, None)  # reset

    update = _make_update(user_id=user_id)
    context = _make_context([])

    await settings_handlers.quick_set_zh(update, context)

    update.message.reply_text.assert_called_once()
    assert user_settings_store.get_target(user_id) == "zh"
    # Reply phải thông báo target mới
    text = update.message.reply_text.call_args.args[0]
    assert "zh" in text


@pytest.mark.asyncio
async def test_quick_set_da() -> None:
    """`/da` phải set target sang 'da' không cần args."""
    user_id = 2002
    user_settings_store._data.pop(user_id, None)  # reset

    update = _make_update(user_id=user_id)
    context = _make_context([])

    await settings_handlers.quick_set_da(update, context)

    update.message.reply_text.assert_called_once()
    assert user_settings_store.get_target(user_id) == "da"
    text = update.message.reply_text.call_args.args[0]
    assert "da" in text


# === Auto-override target tests ===
# Khi user nhắn tiếng Trung / Đan Mạch, bot phải auto-override target sang 'vi'
# bất kể target setting hiện tại.


def test_resolve_target_chinese_overrides_to_vi() -> None:
    """Text tiếng Trung + target=en → phải override thành 'vi'."""
    from tele_bot_dich.handlers.translate import _resolve_target_lang

    text_zh = "你好，今天天气怎么样"  # Xin chào, hôm nay thời tiết thế nào
    effective, override = _resolve_target_lang(text_zh, "en")
    assert effective == "vi"
    assert override == "zh"


def test_resolve_target_danish_overrides_to_vi() -> None:
    """Text tiếng Đan Mạch + target=fr → phải override thành 'vi'."""
    from tele_bot_dich.handlers.translate import _resolve_target_lang

    text_da = "Hej, hvordan har du det i dag og hvad skal vi lave"  # Nhiều stopwords
    effective, override = _resolve_target_lang(text_da, "fr")
    assert effective == "vi"
    assert override == "da"


def test_resolve_target_vietnamese_keeps_setting() -> None:
    """Text tiếng Việt → giữ nguyên target setting (không override)."""
    from tele_bot_dich.handlers.translate import _resolve_target_lang

    text_vi = "Xin chào bạn, hôm nay bạn có khỏe không"
    effective, override = _resolve_target_lang(text_vi, "en")
    assert effective == "en"
    assert override is None


def test_resolve_target_english_keeps_setting() -> None:
    """Text ASCII (English) → giữ nguyên target setting."""
    from tele_bot_dich.handlers.translate import _resolve_target_lang

    text_en = "Hello world how are you today my friend"
    effective, override = _resolve_target_lang(text_en, "vi")
    assert effective == "vi"
    assert override is None


def test_resolve_target_no_override_if_already_vi() -> None:
    """Text zh + target đã là 'vi' → không cần override (giữ nguyên)."""
    from tele_bot_dich.handlers.translate import _resolve_target_lang

    text_zh = "你好朋友，欢迎来到这里"
    effective, override = _resolve_target_lang(text_zh, "vi")
    assert effective == "vi"
    # override_source vẫn trả về 'zh' vì detected, nhưng target không đổi
    # → hành vi override "no-op" (không log)


@pytest.mark.asyncio
async def test_handle_text_chinese_forces_target_vi() -> None:
    """Khi nhắn tiếng Trung, translator phải được gọi với target='vi'."""
    from tele_bot_dich.handlers import translate as translate_handler

    # Setup: user có target=en, nhưng nhắn tiếng Trung → phải dịch sang vi
    user_id = 3001
    user_settings_store._data.pop(user_id, None)
    user_settings_store.set_target(user_id, "en")

    # Mock translator
    mock_translator = MagicMock()
    mock_result = MagicMock()
    mock_result.source_lang = "zh"
    mock_result.target_lang = "vi"
    mock_result.translated = "Xin chào"
    mock_translator.translate = AsyncMock(return_value=mock_result)
    translate_handler.set_translator(mock_translator)

    # Mock update
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.username = "tester"
    update.effective_chat = MagicMock()
    update.effective_chat.id = user_id
    update.message = MagicMock()
    update.message.text = "你好世界，欢迎来到这里"
    update.message.reply_text = AsyncMock()

    # Mock context
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    context.args = []

    await translate_handler.handle_text(update, context)

    # Verify: translator được gọi với target='vi' (KHÔNG phải 'en')
    call_kwargs = mock_translator.translate.call_args.kwargs
    assert call_kwargs["target_lang"] == "vi", (
        f"Expected target_lang='vi' (override), got {call_kwargs['target_lang']!r}"
    )


@pytest.mark.asyncio
async def test_handle_text_danish_forces_target_vi() -> None:
    """Khi nhắn tiếng Đan Mạch, translator phải được gọi với target='vi'."""
    from tele_bot_dich.handlers import translate as translate_handler

    user_id = 3002
    user_settings_store._data.pop(user_id, None)
    user_settings_store.set_target(user_id, "ja")  # target khác vi

    mock_translator = MagicMock()
    mock_result = MagicMock()
    mock_result.source_lang = "da"
    mock_result.target_lang = "vi"
    mock_result.translated = "Xin chào"
    mock_translator.translate = AsyncMock(return_value=mock_result)
    translate_handler.set_translator(mock_translator)

    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.username = "tester"
    update.effective_chat = MagicMock()
    update.effective_chat.id = user_id
    update.message = MagicMock()
    update.message.text = "Hej, hvordan har du det i dag og hvad skal vi lave"
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    context.args = []

    await translate_handler.handle_text(update, context)

    call_kwargs = mock_translator.translate.call_args.kwargs
    assert call_kwargs["target_lang"] == "vi", (
        f"Expected target_lang='vi' (override), got {call_kwargs['target_lang']!r}"
    )


@pytest.mark.asyncio
async def test_handle_text_vietnamese_keeps_user_target() -> None:
    """Khi nhắn tiếng Việt, dùng target setting (vd: 'en')."""
    from tele_bot_dich.handlers import translate as translate_handler

    user_id = 3003
    user_settings_store._data.pop(user_id, None)
    user_settings_store.set_target(user_id, "en")

    mock_translator = MagicMock()
    mock_result = MagicMock()
    mock_result.source_lang = "vi"
    mock_result.target_lang = "en"
    mock_result.translated = "Hello"
    mock_translator.translate = AsyncMock(return_value=mock_result)
    translate_handler.set_translator(mock_translator)

    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.username = "tester"
    update.effective_chat = MagicMock()
    update.effective_chat.id = user_id
    update.message = MagicMock()
    update.message.text = "Xin chào bạn, hôm nay bạn có khỏe không"
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    context.args = []

    await translate_handler.handle_text(update, context)

    call_kwargs = mock_translator.translate.call_args.kwargs
    assert call_kwargs["target_lang"] == "en", (
        f"Expected target_lang='en' (no override), got {call_kwargs['target_lang']!r}"
    )
