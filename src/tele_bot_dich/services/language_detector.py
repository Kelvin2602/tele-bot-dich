"""Fallback language detection dùng khi OpenAI không phát hiện được.

Triển khai theo dạng *pluggable*: mặc định dùng heuristic đơn giản (các ký tự
Unicode phổ biến) để tránh thêm dependency `langdetect`. Người dùng có thể
inject detector khác qua constructor của OpenAITranslator (không bắt buộc).

Có 2 tầng heuristic:
1. **Unicode range matching** — phủ Nhật (Hiragana/Katakana), Trung (CJK),
   Hàn (Hangul), Nga (Cyrillic), Ả Rập, Hindi, Thái.
2. **Character hint matching** — phủ tiếng Việt có dấu.
"""

from __future__ import annotations

from tele_bot_dich.utils.logger import logger

# Bảng ánh xạ ký tự đầu → mã ngôn ngữ ISO 639-1 (chỉ dùng khi fallback).
_SCRIPT_HEURISTICS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("vi", ("ă", "â", "đ", "ê", "ô", "ơ", "ư", "Ă", "Â", "Đ", "Ê", "Ô", "Ơ", "Ư")),
    ("zh", ("一", "是", "我", "你", "他", "的", "了", "中", "文")),
    ("ja", ("ひ", "ら", "が", "な", "だ", "です", "ます", "こんにちは")),
    ("ko", ("ㄱ", "ㄴ", "안", "녕", "하", "세", "요")),
    ("ar", ("ا", "ب", "ت", "ث", "ج", "ح", "خ")),
    ("ru", ("ы", "ё", "ъ", "э", "я", "ч", "ш", "щ")),
    ("hi", ("क", "ख", "ग", "ह", "म", "न")),
    ("th", ("ก", "ข", "ค", "ง", "จ")),
)


def _classify_codepoint(cp: int) -> str | None:
    """Phân loại ngôn ngữ dựa trên Unicode code point range.

    Trả về mã ISO 639-1 hoặc None nếu không thuộc script đặc biệt nào.
    """
    # Hiragana (U+3040–U+309F) + Katakana (U+30A0–U+30FF) → Nhật
    if 0x3040 <= cp <= 0x30FF:
        return "ja"
    # Hangul Syllables (U+AC00–U+D7AF) + Hangul Jamo (U+1100–U+11FF) → Hàn
    if 0x1100 <= cp <= 0x11FF or 0xAC00 <= cp <= 0xD7AF:
        return "ko"
    # CJK Unified Ideographs (U+4E00–U+9FFF) — chung cho Trung/Nhật;
    # ưu tiên Nhật nếu đã có Hiragana/Katakana, ngược lại là Trung
    if 0x4E00 <= cp <= 0x9FFF:
        return "zh"  # sẽ bị override bởi 'ja' nếu đã có hiragana/katakana
    # Cyrillic (U+0400–U+04FF) → Nga (mặc định)
    if 0x0400 <= cp <= 0x04FF:
        return "ru"
    # Arabic (U+0600–U+06FF) → Ả Rập
    if 0x0600 <= cp <= 0x06FF:
        return "ar"
    # Devanagari (U+0900–U+097F) → Hindi
    if 0x0900 <= cp <= 0x097F:
        return "hi"
    # Thai (U+0E00–U+0E7F)
    if 0x0E00 <= cp <= 0x0E7F:
        return "th"
    return None


def detect_language_fallback(text: str) -> str:
    """Phỏng đoán ngôn ngữ từ text bằng heuristic Unicode.

    Args:
        text: Văn bản đầu vào.

    Returns:
        Mã ISO 639-1 nếu đoán được, ngược lại ``"auto"``.
    """
    if not text or not text.strip():
        return "auto"

    sample = text[:500]
    scores: dict[str, int] = {}

    # Tầng 1: character hints (đặc trưng cho từng ngôn ngữ)
    for char in sample:
        for code, hints in _SCRIPT_HEURISTICS:
            if char in hints:
                scores[code] = scores.get(code, 0) + 1

    # Tầng 2: Unicode range (phủ rộng hơn)
    has_ja_marker = False
    for char in sample:
        code = _classify_codepoint(ord(char))
        if code is None:
            continue
        if code == "ja":
            has_ja_marker = True
        scores[code] = scores.get(code, 0) + 1

    # Tầng 3: stopwords cho Latin-script languages (Đan Mạch, Pháp, Đức, Tây Ban Nha, Nga translit...)
    # Trọng số thấp hơn char hint để tránh "ăn" nhầm tiếng Việt.
    sample_lower = sample.lower()
    for code, words in _STOPWORDS.items():
        # Bỏ qua 'vi' ở đây vì tiếng Việt đã có char hint (ă, â, đ, ư...).
        if code == "vi":
            continue
        for w in words:
            if w in sample_lower:
                scores[code] = scores.get(code, 0) + 1

    # Nếu có Hiragana/Katakana → chắc chắn là Nhật (kể cả khi có CJK chung)
    if has_ja_marker:
        return "ja"

    if not scores:
        # Heuristic: nếu chỉ toàn ASCII → khả năng cao là Latin-script (en/fr/de/es/...)
        # Nhưng không đủ tự tin để khẳng định, trả về "auto".
        if all(ord(c) < 128 for c in sample.strip()):
            return "auto"
        return "auto"

    # Ngưỡng tối thiểu: nếu score cao nhất quá thấp → trả về 'auto'
    # (tránh false positive từ Latin stopwords ngắn như 'o', 'a', 'e').
    best = max(scores, key=scores.get)
    best_score = scores[best]
    if best_score < 3:
        logger.debug("Score too low ({}), returning 'auto'", best_score)
        return "auto"

    logger.debug("Heuristic detection: {} (scores={})", best, scores)
    return best


# Stopwords phổ biến cho Latin-script languages (lowercase).
# Từ càng phổ biến → trọng số càng cao.
_STOPWORDS: dict[str, tuple[str, ...]] = {
    "da": ("og", "er", "jeg", "det", "at", "har", "hej", "tak", "hvad", "hvordan"),
    "sv": ("och", "är", "jag", "det", "att", "har", "hej", "tack", "vad"),
    "no": ("og", "er", "jeg", "det", "at", "har", "hei", "takk", "hva"),
    "de": ("und", "ist", "ich", "das", "nicht", "ein", "haben", "hallo", "danke"),
    "es": ("y", "es", "el", "que", "hola", "gracias", "buenos", "buenas"),
    "fr": ("et", "est", "je", "tu", "le", "de", "bonjour", "merci", "comment"),
    "it": ("e", "è", "io", "tu", "il", "di", "ciao", "grazie", "come"),
    "nl": ("en", "is", "ik", "het", "niet", "een", "hallo", "dank", "hoe"),
    "pt": ("e", "é", "eu", "você", "o", "de", "olá", "obrigado", "como"),
}


__all__ = ["detect_language_fallback"]
