"""Handler cho /set_target, /target, /settings và quick set commands.

Phiên bản text-only: không có callback handler, không có InlineKeyboard.
"""

from __future__ import annotations

import re

from telegram import Update
from telegram.ext import ContextTypes

from tele_bot_dich.models.user_settings import user_settings_store
from tele_bot_dich.utils.logger import logger

# ISO 639-1 là 2 chữ cái thường (cho phép 'zh', 'en'...). Đơn giản hoá pattern.
_LANG_PATTERN = re.compile(r"^[a-z]{2}$")

# Một số mã phổ biến gợi ý trong /settings (chỉ mang tính gợi ý, không giới hạn).
_COMMON_LANGS: tuple[tuple[str, str], ...] = (
    ("vi", "Tiếng Việt"),
    ("en", "English"),
    ("zh", "中文"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("es", "Español"),
    ("ru", "Русский"),
    ("th", "ไทย"),
)


async def _apply_target(update: Update, lang: str, quick_label: str | None = None) -> None:
    """Helper: áp dụng target lang cho user, phản hồi + log.

    Args:
        update: Update từ Telegram.
        lang: Mã ngôn ngữ ISO 639-1 (đã validate).
        quick_label: Nhãn nguồn (vd: '/zh', '/da') nếu là quick command.
    """
    user_id = update.effective_user.id if update.effective_user else 0
    user_settings_store.set_target(user_id, lang)
    src = quick_label or "/set_target"
    logger.info("SET_TARGET user={} lang={} via={}", user_id, lang, src)
    await update.message.reply_text(  # type: ignore[union-attr]
        f"✅ Đã đặt ngôn ngữ đích: <b>{lang}</b>",
        parse_mode="HTML",
    )


async def set_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý /set_target <code>."""
    if not update.message or not update.effective_user:
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "⚠️ Cú pháp: /set_target &lt;mã_ngôn_ngữ&gt;\n"
            "Ví dụ: /set_target vi, /set_target en",
            parse_mode="HTML",
        )
        return

    lang = args[0].strip().lower()
    if not _LANG_PATTERN.match(lang):
        await update.message.reply_text(
            "❌ Mã ngôn ngữ không hợp lệ. Vui lòng dùng mã ISO 639-1 gồm 2 chữ cái "
            "(vd: vi, en, ja, zh, ko, fr, de).",
            parse_mode="HTML",
        )
        return

    await _apply_target(update, lang)


# --- Quick set commands: shortcut cho các ngôn ngữ hay dùng ---


async def quick_set_zh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """`/zh` — set target sang Tiếng Trung (zh)."""
    if not update.message or not update.effective_user:
        return
    await _apply_target(update, "zh", quick_label="/zh")


async def quick_set_da(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """`/da` — set target sang Tiếng Đan Mạch (da)."""
    if not update.message or not update.effective_user:
        return
    await _apply_target(update, "da", quick_label="/da")


async def show_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý /target."""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    current = user_settings_store.get_target(user_id)
    logger.info("SHOW_TARGET user={} current={}", user_id, current)
    await update.message.reply_text(
        f"🌐 Ngôn ngữ đích hiện tại: <b>{current}</b>",
        parse_mode="HTML",
    )


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý /settings — hiển thị cấu hình + gợi ý ngôn ngữ.

    Text-only, không có InlineKeyboard (theo yêu cầu dự án).
    """
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    current = user_settings_store.get_target(user_id)

    # Build gợi ý ngôn ngữ (mỗi dòng 1 ngôn ngữ)
    lines = [
        "⚙️ <b>Cài đặt</b>",
        "",
        f"🌐 Ngôn ngữ đích hiện tại: <b>{current}</b>",
        "",
        "<b>Đổi ngôn ngữ đích:</b>",
        "Gõ <code>/set_target &lt;mã&gt;</code> với mã ISO 639-1 bất kỳ.",
        "Ví dụ: <code>/set_target en</code>",
        "",
        "<b>Quick set:</b> /zh (Trung) · /da (Đan Mạch)",
        "",
        "<b>Một số mã phổ biến:</b>",
    ]
    for code, name in _COMMON_LANGS:
        marker = " ✓" if code == current else ""
        lines.append(f"  • <code>{code}</code> — {name}{marker}")
    lines.extend([
        "",
        "Gõ /help để xem tất cả lệnh.",
    ])
    logger.info("SETTINGS user={} current={}", user_id, current)
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


__all__ = ["set_target", "show_target", "show_settings", "quick_set_zh", "quick_set_da"]
