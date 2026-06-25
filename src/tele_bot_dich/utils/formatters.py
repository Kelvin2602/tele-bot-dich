"""Helpers format & escape text cho Telegram MarkdownV2."""

from __future__ import annotations

# Ký tự đặc biệt cần escape trong MarkdownV2 theo docs Telegram
_MD2_SPECIAL = set("_*[]()~`>#+-=|{}.!")


def escape_md2(text: str) -> str:
    """Escape các ký tự đặc biệt để dùng an toàn với parse_mode=MarkdownV2.

    Args:
        text: Chuỗi gốc.

    Returns:
        Chuỗi đã được escape (thêm `\\` trước ký tự đặc biệt).
    """
    if not text:
        return ""
    return "".join(f"\\{c}" if c in _MD2_SPECIAL else c for c in text)


def format_translation_reply(
    source_lang: str, target_lang: str, translated: str
) -> str:
    """Tạo message trả lời sau khi dịch.

    Args:
        source_lang: Mã ngôn ngữ nguồn (ISO 639-1).
        target_lang: Mã ngôn ngữ đích.
        translated: Nội dung bản dịch.

    Returns:
        Chuỗi đã escape, sẵn sàng gửi với parse_mode=MarkdownV2.
    """
    src = escape_md2(source_lang.upper())
    tgt = escape_md2(target_lang.upper())
    body = escape_md2(translated)
    return f"🌍 *{src}* → *{tgt}*\n\n{body}"


__all__ = ["escape_md2", "format_translation_reply"]
