"""Handler xử lý tin nhắn văn bản thường (không phải command) → dịch.

Bao gồm:
- `handle_text`: xử lý tin nhắn văn bản → dịch
- `handle_unsupported`: xử lý ảnh/voice/sticker/file → hướng dẫn user
"""

from __future__ import annotations

import asyncio
import time

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from tele_bot_dich.config import settings
from tele_bot_dich.models.user_settings import user_settings_store
from tele_bot_dich.services.language_detector import detect_language_fallback
from tele_bot_dich.services.openai_translator import (
    OpenAITranslator,
    TranslationError,
)
from tele_bot_dich.services.rate_limiter import get_rate_limiter
from tele_bot_dich.utils.formatters import format_translation_reply
from tele_bot_dich.utils.logger import logger

# Singleton translator (có thể inject mock trong test qua `app.bot_data`).
_translator: OpenAITranslator | None = None


def get_translator() -> OpenAITranslator:
    """Trả về translator singleton (lazy init)."""
    global _translator
    if _translator is None:
        _translator = OpenAITranslator()
    return _translator


def set_translator(translator: OpenAITranslator) -> None:
    """Inject translator (dùng trong test)."""
    global _translator
    _translator = translator


# Map: source language được phát hiện → target language bắt buộc.
# Khi user nhắn bằng ngôn ngữ "ngoại" này, ý đồ gần như luôn là "dịch giúp
# sang tiếng Việt" — bất kể target setting hiện tại.
# Lưu ý: /zh và /da vẫn hoạt động bình thường để user set target = Trung/Đan Mạch
# khi cần dịch chiều ngược lại (vd: từ Việt → Trung).
_AUTO_TARGET_OVERRIDE: dict[str, str] = {
    "zh": "vi",  # Tiếng Trung → luôn dịch sang Tiếng Việt
    "da": "vi",  # Tiếng Đan Mạch → luôn dịch sang Tiếng Việt
}


def _resolve_target_lang(text: str, user_target: str) -> tuple[str, str | None]:
    """Quyết định target lang thực tế dùng để dịch.

    Logic:
    1. Phát hiện source language bằng heuristic Unicode.
    2. Nếu source ∈ `_AUTO_TARGET_OVERRIDE` và target hiện tại khác → override
       target thành giá trị mặc định (thường là `vi`).
    3. Ngược lại → giữ nguyên target từ user setting.

    Args:
        text: Văn bản đầu vào (đã trim).
        user_target: Target lang hiện tại của user (từ `UserSettingsStore`).

    Returns:
        Tuple `(effective_target, override_source)`:
        - `effective_target`: Target lang sẽ pass cho translator.
        - `override_source`: Mã source language gây ra override, hoặc `None`
          nếu không override.
    """
    detected = detect_language_fallback(text)
    override = _AUTO_TARGET_OVERRIDE.get(detected)
    if override and override != user_target:
        return override, detected
    return user_target, None


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý mọi tin nhắn văn bản không phải command."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id if update.effective_user else 0
    chat_id = update.effective_chat.id if update.effective_chat else user_id
    username = update.effective_user.username if update.effective_user else "?"

    # 1) Validate độ dài
    if not text or len(text) > settings.max_text_length:
        logger.warning("REJECT  user={} text_len={} (limit={})", user_id, len(text), settings.max_text_length)
        await update.message.reply_text(
            f"⚠️ Văn bản phải từ 1 đến {settings.max_text_length} ký tự.",
        )
        return

    # 2) Lấy target lang theo user, áp dụng auto-override nếu source = zh/da
    user_target = user_settings_store.get_target(user_id)
    target, override_src = _resolve_target_lang(text, user_target)
    if override_src:
        logger.info(
            "TARGET_OVR user={} src={} old={} → new=vi (luôn dịch sang Việt)",
            user_id, override_src, user_target,
        )

    # Log incoming
    logger.info("RECV    user={} (@{}) target={} text={!r}", user_id, username, target, text[:80])

    # 3) Kiểm tra rate limit
    rl = get_rate_limiter().check(user_id)
    if not rl.allowed:
        logger.warning(
            "RATE_LIMIT user={} remaining={} reset_after={:.0f}s",
            user_id, rl.remaining, rl.reset_after,
        )
        await update.message.reply_text(
            f"⏳ Bạn đã gửi quá nhiều yêu cầu. "
            f"Vui lòng đợi {rl.reset_after:.0f} giây trước khi thử lại.",
        )
        return

    # 4) Báo "đang nhập" cho UX tốt hơn + refresh mỗi 4s
    #    (Telegram tự clear typing sau 5s, nên cần gửi lại)
    async def keep_typing() -> None:
        try:
            while True:
                await context.bot.send_chat_action(
                    chat_id=chat_id, action=ChatAction.TYPING
                )
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass
        except Exception as exc:  # noqa: BLE001
            logger.warning("Typing indicator failed: {}", exc)

    typing_task = asyncio.create_task(keep_typing())

    # 5) Gọi translator
    t0 = time.time()
    try:
        result = await get_translator().translate(text=text, target_lang=target)
        elapsed = time.time() - t0
        logger.info(
            "TRANSL  user={} src={} tgt={} time={:.2f}s result={!r}",
            user_id, result.source_lang, result.target_lang, elapsed, result.translated[:80],
        )
    except TranslationError as exc:
        elapsed = time.time() - t0
        logger.error("TRANSFAIL user={} time={:.2f}s err={}", user_id, elapsed, exc)
        await update.message.reply_text(
            f"❌ Xin lỗi, dịch vụ dịch bị timeout sau {elapsed:.0f}s.\n"
            "Vui lòng thử lại sau ít giây.",
        )
        return
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except (asyncio.CancelledError, Exception):
            pass

    if not result.translated:
        logger.warning("EMPTY   user={} model returned empty", user_id)
        await update.message.reply_text("⚠️ Bot nhận được phản hồi rỗng từ dịch vụ dịch.")
        return

    # 6) Gửi kết quả
    reply = format_translation_reply(
        source_lang=result.source_lang,
        target_lang=result.target_lang,
        translated=result.translated,
    )
    try:
        await update.message.reply_text(reply, parse_mode="MarkdownV2")
        logger.info("SENT    user={} reply_len={}", user_id, len(reply))
    except Exception as e:
        # Fallback nếu MarkdownV2 lỗi (ký tự đặc biệt)
        logger.warning("MD2_FALLBACK user={} err={}", user_id, e)
        await update.message.reply_text(reply)


async def handle_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hướng dẫn user khi gửi ảnh/voice/sticker/file.

    Bot hiện chỉ hỗ trợ dịch văn bản, nên từ chối nhẹ nhàng và gợi ý gõ /help.
    """
    if not update.message:
        return
    logger.info("Unsupported message type from user {}", update.effective_user.id if update.effective_user else "?")
    await update.message.reply_text(
        "📝 <b>Bot chỉ hỗ trợ dịch văn bản.</b>\n\n"
        "Gửi tin nhắn text bất kỳ để dịch nhé!\n"
        "Gõ /help để xem hướng dẫn.",
        parse_mode="HTML",
    )


__all__ = [
    "handle_text",
    "handle_unsupported",
    "get_translator",
    "set_translator",
    "_AUTO_TARGET_OVERRIDE",
    "_resolve_target_lang",
]
