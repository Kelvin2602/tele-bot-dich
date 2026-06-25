"""Đăng ký danh sách lệnh (Menu) cho Telegram bot.

Khi gọi `set_my_commands`, Telegram client sẽ hiển thị nút "Menu" ngay
cạnh thanh nhập tin nhắn. Click vào sẽ mở danh sách các lệnh này.

Mỗi lệnh gồm:
- `command`: tên lệnh (không bao gồm `/`)
- `description`: mô tả ngắn (1-3 từ, Telegram giới hạn ~256 ký tự)
"""

from __future__ import annotations

from telegram import Bot, BotCommand


# Danh sách lệnh hiển thị trong Menu (cạnh thanh nhập tin nhắn).
# Thứ tự hiển thị đúng thứ tự trong list.
BOT_COMMANDS: list[BotCommand] = [
    BotCommand("start", "Khởi động bot"),
    BotCommand("help", "Xem hướng dẫn"),
    BotCommand("settings", "Cài đặt ngôn ngữ đích"),
    BotCommand("target", "Xem ngôn ngữ đích hiện tại"),
    BotCommand("set_target", "Đặt ngôn ngữ đích (vd: /set_target en)"),
    # Quick set commands (shortcut)
    BotCommand("zh", "Dịch sang Tiếng Trung (中文)"),
    BotCommand("da", "Dịch sang Tiếng Đan Mạch (Dansk)"),
]


async def setup_bot_commands(bot: Bot) -> None:
    """Đăng ký danh sách lệnh với Telegram.

    Gọi 1 lần khi bot khởi động. Sau đó, client sẽ hiển thị nút "Menu"
    cạnh thanh nhập tin nhắn chứa các lệnh trong `BOT_COMMANDS`.

    Args:
        bot: Instance `telegram.Bot` từ `app.bot`.
    """
    await bot.set_my_commands(commands=BOT_COMMANDS)


__all__ = ["BOT_COMMANDS", "setup_bot_commands"]
