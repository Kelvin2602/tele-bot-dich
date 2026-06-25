"""Handler cho /start và /help.

Phiên bản text-only, không có InlineKeyboard.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

WELCOME = (
    "👋 <b>Chào mừng đến với Translation Bot</b>\n\n"
    "Gửi bất kỳ văn bản nào để tôi dịch sang ngôn ngữ bạn chọn.\n\n"
    "<b>Các lệnh:</b>\n"
    "• /help — Xem hướng dẫn\n"
    "• /settings — Cài đặt ngôn ngữ đích\n"
    "• /set_target &lt;code&gt; — Đặt ngôn ngữ đích (vd: vi, en, ja)\n"
    "• /target — Xem ngôn ngữ đích hiện tại\n"
    "• /zh — Set nhanh: dịch sang Tiếng Trung\n"
    "• /da — Set nhanh: dịch sang Tiếng Đan Mạch\n\n"
    "💡 <i>Bấm nút Menu cạnh thanh nhập tin nhắn để mở nhanh lệnh.</i>"
)

HELP = (
    "📖 <b>Hướng dẫn sử dụng</b>\n\n"
    "<b>Cách dùng:</b>\n"
    "1. Đặt ngôn ngữ đích: <code>/set_target en</code>\n"
    "2. Gửi bất kỳ văn bản nào, bot sẽ tự phát hiện ngôn ngữ nguồn và dịch.\n\n"
    "<b>Lệnh khả dụng:</b>\n"
    "• /start — Chào mừng\n"
    "• /help — Trợ giúp này\n"
    "• /settings — Cài đặt ngôn ngữ đích (kèm gợi ý mã phổ biến)\n"
    "• /set_target &lt;code&gt; — Đặt ngôn ngữ đích\n"
    "• /target — Xem ngôn ngữ đích hiện tại\n"
    "• /zh — Set nhanh: dịch sang Tiếng Trung (中文)\n"
    "• /da — Set nhanh: dịch sang Tiếng Đan Mạch (Dansk)\n\n"
    "<b>Mẹo:</b> dùng bất kỳ mã ISO 639-1 nào: vi, en, ja, zh, ko, fr, de, es, ru, th...\n"
    "Giới hạn: tối đa 4000 ký tự / tin nhắn."
)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý /start."""
    if not update.message:
        return
    await update.message.reply_text(WELCOME, parse_mode="HTML")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý /help — text only, không có nút bấm."""
    if not update.message:
        return
    await update.message.reply_text(HELP, parse_mode="HTML")


__all__ = ["handle", "help_cmd"]
