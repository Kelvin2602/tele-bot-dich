"""Build & wire Telegram Application."""

from __future__ import annotations

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from tele_bot_dich.config import settings
from tele_bot_dich.handlers import settings as settings_handlers
from tele_bot_dich.handlers import start as start_handlers
from tele_bot_dich.handlers import translate as translate_handlers
from tele_bot_dich.utils.logger import logger


def build_application() -> Application:
    """Tạo Application đã đăng ký đầy đủ handler.

    Returns:
        Application chưa khởi động (chưa `run_polling`).
    """
    logger.info("Building Telegram Application...")
    app = Application.builder().token(settings.telegram_bot_token).build()

    # Commands
    app.add_handler(CommandHandler("start", start_handlers.handle))
    app.add_handler(CommandHandler("help", start_handlers.help_cmd))
    app.add_handler(CommandHandler("settings", settings_handlers.show_settings))
    app.add_handler(CommandHandler("set_target", settings_handlers.set_target))
    app.add_handler(CommandHandler("target", settings_handlers.show_target))
    # Quick set commands (shortcut cho ngôn ngữ hay dùng)
    app.add_handler(CommandHandler("zh", settings_handlers.quick_set_zh))
    app.add_handler(CommandHandler("da", settings_handlers.quick_set_da))

    # Tin nhắn văn bản (loại trừ command)
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            translate_handlers.handle_text,
        )
    )

    # Tin nhắn không hỗ trợ (ảnh, voice, sticker, file, ...)
    # Phải đặt SAU filters.TEXT để không chặn tin nhắn văn bản.
    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.VOICE | filters.VIDEO | filters.Sticker.ALL
            | filters.ANIMATION | filters.Document.ALL,
            translate_handlers.handle_unsupported,
        )
    )

    logger.info("Handlers registered. Ready to run.")
    return app


__all__ = ["build_application"]
