"""Entry point: `python -m tele_bot_dich`.

Hỗ trợ 2 chế độ:
- **Polling** (mặc định) — dùng cho dev local.
- **Webhook** — dùng cho production (Render). Bật bằng `WEBHOOK_ENABLED=true`.
"""

from __future__ import annotations

import os
import sys

from tele_bot_dich.bot import build_application
from tele_bot_dich.commands import setup_bot_commands
from tele_bot_dich.config import settings
from tele_bot_dich.utils.logger import logger, setup_logger


async def _post_init(app) -> None:
    """Hook chạy SAU khi Application khởi tạo, TRƯỚC khi nhận update.

    Dùng để đăng ký Menu button (setMyCommands).
    """
    try:
        await setup_bot_commands(app.bot)
        logger.info("Bot menu commands registered (Menu button shown next to input bar).")
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to register bot commands: {}", exc)


def _run_webhook(app) -> None:
    """Khởi động bot ở chế độ webhook (dùng cho Render / cloud).

    - Render tự động set PORT và RENDER_EXTERNAL_URL.
    - Nếu không có RENDER_EXTERNAL_URL, fallback về `WEBHOOK_URL` trong config.
    """
    port = int(os.environ.get("PORT", settings.webhook_port))
    public_url = (settings.webhook_url or os.environ.get("RENDER_EXTERNAL_URL", "")).rstrip("/")
    if not public_url:
        logger.critical(
            "Webhook mode requires either WEBHOOK_URL or RENDER_EXTERNAL_URL"
        )
        sys.exit(1)

    webhook_full = f"{public_url}{settings.webhook_path}"

    logger.info("Bot is running (webhook). URL={} port={}", webhook_full, port)
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=settings.webhook_path,
        webhook_url=webhook_full,
        secret_token=settings.webhook_secret_token or None,
        allowed_updates=["message"],
    )


def main() -> None:
    """Khởi động bot."""
    setup_logger()
    logger.info("Starting Telegram Translation Bot...")
    try:
        app = build_application()
        app.post_init = _post_init
    except Exception as exc:  # noqa: BLE001
        logger.critical("Failed to build application: {}", exc)
        sys.exit(1)

    if settings.webhook_enabled:
        _run_webhook(app)
    else:
        logger.info("Bot is running (polling). Press Ctrl+C to stop.")
        app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
