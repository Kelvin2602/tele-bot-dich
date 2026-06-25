"""Test cho fallback language detector."""

from __future__ import annotations

from tele_bot_dich.services.language_detector import detect_language_fallback


def test_detect_vietnamese() -> None:
    text = "Xin chào, bạn có khỏe không? Tôi đang học lập trình."
    assert detect_language_fallback(text) == "vi"


def test_detect_chinese() -> None:
    text = "你好世界, 我在学习编程."
    assert detect_language_fallback(text) == "zh"


def test_detect_returns_auto_for_ascii() -> None:
    # ASCII-only thì không phân biệt được en/fr/de → trả về 'auto'
    assert detect_language_fallback("Hello world") == "auto"


def test_detect_returns_auto_for_empty() -> None:
    assert detect_language_fallback("") == "auto"
    assert detect_language_fallback("   ") == "auto"


def test_detect_returns_auto_for_unknown_unicode() -> None:
    # Một số ký tự hiếm không nằm trong bảng heuristic
    assert detect_language_fallback("∑ ∞ ∂") == "auto"
